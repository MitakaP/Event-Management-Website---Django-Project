from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Event, EventCategory, Ticket

User = get_user_model()

class EventModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type=2 
        )
        cls.category = EventCategory.objects.create(name='Test Category')
        cls.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_date='2025-12-31 23:59:00',
            end_date='2026-01-01 01:00:00',
            organizer=cls.user,
            category=cls.category,
            capacity=100,
            price=50.00
        )

    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.organizer.username, 'testuser')
        self.assertEqual(self.event.category.name, 'Test Category')
        self.assertEqual(self.event.available_tickets, 100)

    def test_event_str_method(self):
        self.assertEqual(str(self.event), 'Test Event')

    def test_ticket_creation(self):
        attendee = User.objects.create_user(
            username='attendee',
            password='testpass123',
            user_type=1
        )
        ticket = Ticket.objects.create(
            event=self.event,
            attendee=attendee
        )
        self.assertEqual(ticket.event.title, 'Test Event')
        self.assertEqual(ticket.attendee.username, 'attendee')
        self.assertTrue(ticket.is_active)

class EventViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type=2
        )
        cls.category = EventCategory.objects.create(name='Test Category')
        cls.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_date='2025-12-31 23:59:00',
            end_date='2026-01-01 01:00:00',
            organizer=cls.user,
            category=cls.category,
            capacity=100,
            price=50.00
        )

    def setUp(self):
        self.client = Client()

    def test_event_list_view(self):
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Event')
        self.assertTemplateUsed(response, 'events/event_list.html')

    def test_event_detail_view(self):
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Event')
        self.assertTemplateUsed(response, 'events/event_detail.html')

    def test_event_create_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_create.html')

    def test_event_create_view_unauthenticated(self):
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 302) 

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type=1 
        )

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/registration/login.html')

    def test_successful_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/registration/register.html')

    def test_successful_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'user_type': 1
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())