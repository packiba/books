import json

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='Test book 1', price=25, author_name='author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=50, author_name='bob')
        self.book_3 = Book.objects.create(name='Test book 3', price=60, author_name='author 2')
        self.book_4 = Book.objects.create(name='Test book 4 author 1', price=100,
                                          author_name='author 3')
        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True, rate=5)

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'price': 60})
        books = Book.objects.filter(id=self.book_3.id).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'author 1'})
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_4.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': '-price'})
        books = Book.objects.filter(
            id__in=[self.book_4.id, self.book_3.id, self.book_2.id, self.book_1.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')).order_by(
            '-price')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        response = self.client.get(url, data={'ordering': 'author_name'})
        books = Book.objects.filter(
            id__in=[self.book_1.id, self.book_3.id, self.book_4.id, self.book_2.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')).order_by(
            'author_name')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            "name": "Python 3",
            "price": 150,
            "author_name": "Mark Summerfield"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(5, Book.objects.all().count())

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 555,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.book_1.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(555, self.book_1.price)

    def test_delete(self):
        self.assertEqual(4, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(3, Book.objects.all().count())

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 555,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.book_1.refresh_from_db()

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(25, self.book_1.price)
        self.assertEqual({'detail': ErrorDetail(
            string='You do not have permission to perform this action.', code='permission_denied')},
            response.data)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username2', is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 555,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.book_1.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(555, self.book_1.price)


class BooksRelationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')
        self.book_1 = Book.objects.create(name='Test book 1', price=25, author_name='author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=50, author_name='bob')

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "like": True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertTrue(relation.like)

    def test_in_bookmarks(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "in_bookmarks": True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "rate": 5
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertEqual(5, relation.rate)

    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "rate": 7
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
