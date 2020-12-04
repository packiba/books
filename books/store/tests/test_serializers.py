from django.contrib.auth.models import User
from django.db.models import Count, Case, When, F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username='IvPet', first_name='Ivan', last_name='Petrov')
        user2 = User.objects.create(username='user2', first_name='Oleg', last_name='Ivanov')
        user3 = User.objects.create(username='user3', first_name='1', last_name='2')

        book_1 = Book.objects.create(name='Test book 1', price=50, author_name='author 1',
                                          owner=user1)
        book_2 = Book.objects.create(name='Test book 2', price=60, author_name='author 2')

        UserBookRelation.objects.create(user=user1, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user3, book=book_1, like=True, rate=4)

        UserBookRelation.objects.create(user=user1, book=book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True, rate=4)
        UserBookRelation.objects.create(user=user3, book=book_2, like=False)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).order_by('id')
        data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'name': 'Test book 1',
                'price': '50.00',
                'author_name': 'author 1',
                'annotated_likes': 3,
                'rating': '4.67',
                'owner_name': 'IvPet',
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Petrov',
                    },
                    {
                        'first_name': 'Oleg',
                        'last_name': 'Ivanov',
                    },
                    {
                        'first_name': '1',
                        'last_name': '2',
                    }
                ]
            },
            {
                'id': book_2.id,
                'name': 'Test book 2',
                'price': '60.00',
                'author_name': 'author 2',
                'annotated_likes': 2,
                'rating': '3.50',
                'owner_name': '',
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Petrov',
                    },
                    {
                        'first_name': 'Oleg',
                        'last_name': 'Ivanov',
                    },
                    {
                        'first_name': '1',
                        'last_name': '2',
                    }
                ]
            }
        ]
        self.assertEqual(expected_data, data)
