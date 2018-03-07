from formtools.wizard.views import NamedUrlSessionWizardView

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.urlresolvers import reverse

from pombola.core.models import Person, Organisation

from .forms import RecipientForm, DraftForm, PreviewForm
from .client import WriteInPublic
from .models import Configuration


def person_everypolitician_uuid_required(function):
    def wrap(request, *args, **kwargs):
        person = Person.objects.get(slug=kwargs['person_slug'])
        if person.everypolitician_uuid is None:
            raise Http404("Person is missing an EveryPolitician UUID")
        else:
            return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


class PersonAdapter(object):
    def filter(self, ids):
        return Person.objects.filter(
            identifiers__scheme='everypolitician',
            identifiers__identifier__in=ids,
        )

    def get(self, object_id):
        return Person.objects.get(
            identifiers__scheme='everypolitician',
            identifiers__identifier=object_id,
        )

    def get_by_id(self, object_id):
        return Person.objects.get(pk=object_id)

    def get_form_kwargs(self, step=None):
        step_form_kwargs = {
            'recipients': {
                'queryset': Person.objects.filter(
                    identifiers__scheme='everypolitician',
                    identifiers__identifier__isnull=False,
                ),
            },
        }
        return step_form_kwargs.get(step, {})

    def object_ids(self, objects):
        return [p.everypolitician_uuid for p in objects]

    def get_templates(self):
        return {
            'recipients': 'writeinpublic/person-write-recipients.html',
            'draft': 'writeinpublic/person-write-draft.html',
            'preview': 'writeinpublic/person-write-preview.html',
        }


class CommitteeAdapter(object):
    def filter(self, ids):
        return Organisation.objects.filter(id__in=ids)

    def get(self, object_id):
        return Organisation.objects.get(pk=object_id)

    def get_by_id(self, object_id):
        return self.get(object_id)

    def get_form_kwargs(self, step=None):
        step_form_kwargs = {
            'recipients': {
                'queryset': Organisation.objects.filter(
                    kind__name='National Assembly Committees',
                    contacts__kind__slug='email'
                ),
                'multiple': False,
            },
        }
        return step_form_kwargs.get(step, {})

    def object_ids(self, objects):
        return [org.id for org in objects]

    def get_templates(self):
        return {
            'recipients': 'writeinpublic/committee-write-recipients.html',
            'draft': 'writeinpublic/committee-write-draft.html',
            'preview': 'writeinpublic/committee-write-preview.html',
        }


class WriteInPublicMixin(object):
    def dispatch(self, *args, **kwargs):
        configuration_slug = kwargs['configuration_slug']
        configuration = Configuration.objects.get(slug=configuration_slug)

        # FIXME: It would be nice if we didn't hardcode the configuration_slug
        # values here.
        if configuration_slug == 'south-africa-assembly':
            self.adapter = PersonAdapter()
        elif configuration_slug == 'south-africa-committees':
            self.adapter = CommitteeAdapter()
        else:
            raise Exception, "Unknown configuration_slug: {}".format(configuration_slug)

        self.client = WriteInPublic(
            configuration.url,
            configuration.username,
            configuration.api_key,
            configuration.instance_id,
            configuration.person_uuid_prefix,
            adapter=self.adapter
        )
        return super(WriteInPublicMixin, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        self.request.current_app = self.request.resolver_match.namespace
        return super(WriteInPublicMixin, self).render_to_response(context, **response_kwargs)


FORMS = [
    ("recipients", RecipientForm),
    ("draft", DraftForm),
    ("preview", PreviewForm),
]


class WriteInPublicNewMessage(WriteInPublicMixin, NamedUrlSessionWizardView):
    form_list = FORMS

    def get_form_kwargs(self, step=None):
        return self.adapter.get_form_kwargs(step=step)

    def get(self, *args, **kwargs):
        step = kwargs.get('step')
        # If we have an ID in the URL and it matches someone, go straight to
        # /draft
        if 'person_id' in self.request.GET:
            person_id = self.request.GET['person_id']
            try:
                recipient = self.adapter.get_by_id(person_id)
                self.storage.set_step_data('recipients', {'recipients-persons': [recipient.id]})
                self.storage.current_step = 'draft'
                return redirect(self.get_step_url('draft'))
            except Person.DoesNotExist:
                pass

        # Check that the form contains valid data
        if step == 'draft' or step == 'preview':
            recipients = self.get_cleaned_data_for_step('recipients')
            if recipients is None or recipients.get('persons') == []:
                # Form is missing persons, restart process
                self.storage.reset()
                self.storage.current_step = self.steps.first
                return redirect(self.get_step_url(self.steps.first))

        return super(WriteInPublicNewMessage, self).get(*args, **kwargs)

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={'step': step}, current_app=self.request.resolver_match.namespace)

    def get_template_names(self):
        return [self.adapter.get_templates()[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super(WriteInPublicNewMessage, self).get_context_data(form=form, **kwargs)
        context['message'] = self.get_cleaned_data_for_step('draft')
        recipients = self.get_cleaned_data_for_step('recipients')
        if recipients is not None:
            context['persons'] = recipients.get('persons')
        return context

    def done(self, form_list, form_dict, **kwargs):
        persons = form_dict['recipients'].cleaned_data['persons']
        person_ids = self.adapter.object_ids(persons)
        message = form_dict['draft'].cleaned_data
        try:
            response = self.client.create_message(
                author_name=message['author_name'],
                author_email=message['author_email'],
                subject=message['subject'],
                content=message['content'],
                persons=person_ids,
            )
            if response.ok:
                message_id = response.json()['id']
                messages.success(self.request, 'Success, your message has been accepted.')
                return redirect(reverse('writeinpublic:writeinpublic-pending', current_app=self.request.resolver_match.namespace))
            else:
                messages.error(self.request, 'Sorry, there was an error sending your message, please try again. If this problem persists please contact us.')
                return redirect(reverse('writeinpublic:writeinpublic-new-message', current_app=self.request.resolver_match.namespace))
        except self.client.WriteInPublicException:
            messages.error(self.request, 'Sorry, there was an error connecting to the message service, please try again. If this problem persists please contact us.')
            return redirect(reverse('writeinpublic:writeinpublic-new-message', current_app=self.request.resolver_match.namespace))


class WriteInPublicMessage(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/message.html'

    def get_context_data(self, **kwargs):
        context = super(WriteInPublicMessage, self).get_context_data(**kwargs)
        context['message'] = self.client.get_message(self.kwargs['message_id'])
        return context


class WriteToRepresentativeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/messages.html'

    @method_decorator(person_everypolitician_uuid_required)
    def dispatch(self, *args, **kwargs):
        return super(WriteToRepresentativeMessages, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WriteToRepresentativeMessages, self).get_context_data(**kwargs)
        person_slug = self.kwargs['person_slug']
        person = get_object_or_404(Person, slug=person_slug)
        context['person'] = person
        if person.everypolitician_uuid is None:
            context['messages'] = []
        else:
            person_uri = 'https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-{}'.format(person.everypolitician_uuid)
            context['messages'] = self.client.get_messages(person_uri)
        return context

class WriteToCommitteeMessages(WriteInPublicMixin, TemplateView):
    template_name = 'writeinpublic/committee-messages.html'

    def get_context_data(self, **kwargs):
        context = super(WriteToCommitteeMessages, self).get_context_data(**kwargs)
        slug = self.kwargs['slug']
        committee = get_object_or_404(Organisation, slug=slug)
        context['committee'] = committee
        uri = self.client.person_uuid_prefix.format(committee.id)
        context['messages'] = self.client.get_messages(uri)
        return context
