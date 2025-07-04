import unittest
from flask_testing import TestCase
from app import app, db, User

class BasicTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register(self):
        with self.client:
            response = self.client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'testpass123'
            }, follow_redirects=True)
            self.assertIn(b'Registro exitoso', response.data)

    def test_login(self):
        user = User(username='testuser', email='test@example.com', password_hash='123456')
        db.session.add(user)
        db.session.commit()
        with self.client:
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': '123456'
            }, follow_redirects=True)
            self.assertIn(b'Dashboard', response.data)

if __name__ == '__main__':
    unittest.main() 