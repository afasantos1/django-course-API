"""
Tests for the Ingredients API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsApiTests(TestCase):
    """Tests for unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for API requests."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Tests for authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient(self):
        """Test retrieving for authenticated user"""
        Ingredient.objects.create(user=self.user, name='Caramel')
        Ingredient.objects.create(user=self.user, name='Chocolate')
        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_limited_to_user(self):
        """Test retrieval is limited to user data"""
        user2 = create_user(email='user2@example.com', password='pass123')
        Ingredient.objects.create(user=user2, name='Bread')
        ingredient = Ingredient.objects.create(user=self.user, name='Jam')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        ingredient2 = res.data[0]
        self.assertEqual(ingredient.name, ingredient2['name'])
        self.assertEqual(ingredient.id,    ingredient2['id'])

    def test_update_ingredient(self):
        """Test updating of ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Sugar')
        payload = {'name': 'Honey'}
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredients(self):
        """Test deleting ingredients"""
        Ingredient.objects.create(user=self.user, name='Onion')
        ingredient = Ingredient.objects.create(user=self.user, name='Carrot')
        url = detail_url(ingredient.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code,  status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.filter(user=self.user).count(), 1)
        self.assertFalse(Ingredient.objects.filter(name='Carrot').exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        in1 = Ingredient.objects.create(user=self.user, name='Apples')
        in2 = Ingredient.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            title='Apple crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Lentils')
        recipe1 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=20,
            price=Decimal('7.00'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Herb Eggs',
            time_minutes=20,
            price=Decimal('4.00'),
            user=self.user,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
