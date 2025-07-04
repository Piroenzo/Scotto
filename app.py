from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
import logging
from logging.handlers import RotatingFileHandler
from flasgger import Swagger
import io
import json
from dotenv import load_dotenv
import threading

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')

# Configuración de base de datos para Render
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///scotto.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'

# Configuración de email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'scottoadm@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'vjbx gvwz erzo cfjw')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

csrf = CSRFProtect(app)

# Modelos de base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    boards = db.relationship('Board', backref='owner', lazy=True)
    board_memberships = db.relationship('BoardMember', backref='user', lazy=True)
    cards = db.relationship('Card', backref='creator', lazy=True, foreign_keys='Card.creator_id')
    assigned_cards = db.relationship('Card', backref='assignee_user', lazy=True, foreign_keys='Card.assignee_id')

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    color = db.Column(db.String(20), default='#667eea')  # Color de fondo del tablero
    
    # Relaciones
    lists = db.relationship('List', backref='board', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('BoardMember', backref='board', lazy=True, cascade='all, delete-orphan')

class BoardMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # owner, admin, member, observer
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    can_edit = db.Column(db.Boolean, default=True)  # True: puede editar, False: solo vista

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, default=0)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    cards = db.relationship('Card', backref='list', lazy=True, cascade='all, delete-orphan')

class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False, default='#667eea')
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    cards = db.relationship('Card', backref='label_obj', lazy=True)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, default=0)
    due_date = db.Column(db.DateTime)
    reminder_date = db.Column(db.DateTime, nullable=True)  # Fecha/hora de recordatorio
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    label_id = db.Column(db.Integer, db.ForeignKey('label.id'), nullable=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Usuario asignado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attachment = db.Column(db.String(255), nullable=True)  # Ruta del archivo adjunto
    
    # Relaciones
    checklist_items = db.relationship('ChecklistItem', backref='card', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='card', lazy=True, cascade='all, delete-orphan')
    assignee = db.relationship('User', foreign_keys=[assignee_id])

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer, default=0)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # Para hilos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='activity_logs')
    board = db.relationship('Board', backref='activity_logs')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Rutas principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Validaciones estrictas
        if not username or len(username) < 3 or len(username) > 80:
            flash('El nombre de usuario debe tener entre 3 y 80 caracteres')
            return redirect(url_for('register'))
        if not email or '@' not in email or len(email) > 120:
            flash('Email inválido')
            return redirect(url_for('register'))
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado')
            return redirect(url_for('register'))
        user = User()
        user.username = username
        user.email = email
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        # Enviar email de bienvenida
        send_welcome_email(user)
        flash('Registro exitoso! Por favor inicia sesión.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener tableros del usuario (propios y compartidos)
    owned_boards = Board.query.filter_by(owner_id=current_user.id).all()
    shared_boards = Board.query.join(BoardMember).filter(BoardMember.user_id == current_user.id).all()
    
    return render_template('dashboard.html', owned_boards=owned_boards, shared_boards=shared_boards)

@app.route('/board/<int:board_id>')
@login_required
def board(board_id):
    board = Board.query.get_or_404(board_id)
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership:
            flash('No tienes acceso a este tablero')
            return redirect(url_for('dashboard'))
    
    lists = List.query.filter_by(board_id=board_id).order_by(List.position).all()
    return render_template('board.html', board=board, lists=lists)

@app.route('/board/<int:board_id>/calendar')
@login_required
def board_calendar(board_id):
    board = Board.query.get_or_404(board_id)
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership:
            flash('No tienes acceso a este tablero')
            return redirect(url_for('dashboard'))
    
    # Obtener todas las tarjetas con fechas de vencimiento
    cards_with_dates = Card.query.join(List).filter(
        List.board_id == board_id,
        Card.due_date.isnot(None)
    ).order_by(Card.due_date).all()
    
    return render_template('calendar.html', board=board, cards=cards_with_dates)

# API Routes para AJAX
@app.route('/api/board', methods=['POST'])
@csrf.exempt
@login_required
def create_board():
    data = request.get_json()
    board = Board(
        title=data['title'],
        description=data.get('description', ''),
        owner_id=current_user.id,
        color=data.get('color', '#667eea')
    )
    db.session.add(board)
    db.session.commit()
    
    # Agregar al creador como miembro
    member = BoardMember(board_id=board.id, user_id=current_user.id, role='owner')
    db.session.add(member)
    db.session.commit()
    
    # Preparar respuesta inmediata
    response_data = {'id': board.id, 'title': board.title, 'description': board.description, 'color': board.color}
    
    # Registrar actividad de forma asíncrona (no bloquea la respuesta)
    def log_activity_background():
        try:
            with app.app_context():
                log = ActivityLog(
                    user_id=current_user.id, 
                    board_id=board.id, 
                    details=f"Crear tablero: Título: {data['title']}"
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    # Ejecutar logging en background
    thread = threading.Thread(target=log_activity_background)
    thread.daemon = True
    thread.start()
    
    return jsonify(response_data)

@app.route('/api/board/<int:board_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
@login_required
def manage_board(board_id):
    try:
        board = Board.query.get_or_404(board_id)
        if board.owner_id != current_user.id:
            return jsonify({'error': 'No tienes permisos'}), 403
        if request.method == 'DELETE':
            try:
                # Eliminar logs de actividad asociados al tablero
                ActivityLog.query.filter_by(board_id=board.id).delete()
                
                # Eliminar miembros del tablero
                BoardMember.query.filter_by(board_id=board.id).delete()
                
                # Eliminar etiquetas del tablero
                Label.query.filter_by(board_id=board.id).delete()
                
                # Eliminar listas y sus tarjetas (cascade)
                for list_item in board.lists:
                    # Eliminar comentarios de las tarjetas
                    for card in list_item.cards:
                        Comment.query.filter_by(card_id=card.id).delete()
                        ChecklistItem.query.filter_by(card_id=card.id).delete()
                    # Eliminar tarjetas
                    Card.query.filter_by(list_id=list_item.id).delete()
                    # Eliminar lista
                    db.session.delete(list_item)
                
                # Finalmente eliminar el tablero
                db.session.delete(board)
                db.session.commit()
                
                return jsonify({'message': 'Tablero eliminado exitosamente'})
            except Exception as e:
                db.session.rollback()
                import traceback
                print(f"Error al eliminar tablero: {e}")
                print(traceback.format_exc())
                return jsonify({'error': 'Error al eliminar tablero', 'message': str(e)}), 500
        data = request.get_json()
        board.title = data['title']
        board.description = data.get('description', '')
        board.color = data.get('color', board.color)
        db.session.commit()
        # Registrar actividad
        log_activity_async(current_user.id, board.id, 'Actualizar tablero', f'Título: {data["title"]}, Descripción: {data["description"] if data["description"] else "Sin descripción"}, Color: {data["color"] if data["color"] else "Sin color"}')
        return jsonify({'id': board.id, 'title': board.title, 'description': board.description, 'color': board.color})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': 'Error interno al borrar/editar tablero', 'message': str(e)}), 500

@app.route('/api/list', methods=['POST'])
@csrf.exempt
@login_required
def create_list():
    data = request.get_json()
    board = Board.query.get_or_404(data['board_id'])
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=data['board_id'], user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos para modificar'}), 403
    
    # Obtener la posición máxima
    max_position = db.session.query(db.func.max(List.position)).filter_by(board_id=data['board_id']).scalar() or 0
    
    list_item = List(title=data['title'], board_id=data['board_id'], position=max_position + 1)
    db.session.add(list_item)
    db.session.commit()
    
    # Preparar respuesta inmediata
    response_data = {'id': list_item.id, 'title': list_item.title, 'position': list_item.position}
    
    # Registrar actividad de forma asíncrona
    def log_activity_background():
        try:
            with app.app_context():
                log = ActivityLog(
                    user_id=current_user.id, 
                    board_id=board.id, 
                    details=f"Crear lista: Título: {data['title']}"
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    # Ejecutar logging en background
    thread = threading.Thread(target=log_activity_background)
    thread.daemon = True
    thread.start()
    
    return jsonify(response_data)

@app.route('/api/list/<int:list_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
@login_required
def manage_list(list_id):
    list_item = List.query.get_or_404(list_id)
    board = db.session.get(Board, list_item.board_id)
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(list_item)
        db.session.commit()
        # Registrar actividad
        log_activity_async(current_user.id, board.id, 'Eliminar lista', f'Título: {list_item.title}')
        return jsonify({'message': 'Lista eliminada'})
    
    data = request.get_json()
    list_item.title = data['title']
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Actualizar lista', f'Título: {data["title"]}')
    return jsonify({'id': list_item.id, 'title': list_item.title})

@app.route('/api/list/<int:list_id>/cards', methods=['GET'])
@login_required
def get_cards(list_id):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    cards_query = Card.query.filter_by(list_id=list_id).order_by(Card.position)
    pagination = cards_query.paginate(page=page, per_page=per_page, error_out=False)
    cards = [
        {
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'position': c.position,
            'priority': c.priority,
            'label_id': c.label_id,
            'due_date': c.due_date.isoformat() if c.due_date else None,
            'reminder_date': c.reminder_date.isoformat() if c.reminder_date else None,
            'attachment': c.attachment,
            'assignee': {'id': c.assignee.id, 'username': c.assignee.username} if getattr(c, 'assignee', None) else None
        }
        for c in pagination.items
    ]
    return jsonify({
        'cards': cards,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })

@app.route('/api/card', methods=['POST'])
@csrf.exempt
@login_required
def create_card():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form
        file = request.files.get('attachment')
    else:
        data = request.get_json()
        file = None
    # Validaciones estrictas
    if not data.get('title') or len(data['title']) < 3 or len(data['title']) > 200:
        return jsonify({'error': 'El título debe tener entre 3 y 200 caracteres'}), 400
    if data.get('due_date'):
        try:
            due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            if due_date < datetime.utcnow():
                return jsonify({'error': 'La fecha de vencimiento debe ser futura'}), 400
        except Exception:
            return jsonify({'error': 'Formato de fecha de vencimiento inválido'}), 400
    if data.get('reminder_date'):
        try:
            reminder_date = datetime.fromisoformat(data['reminder_date'].replace('Z', '+00:00'))
            if reminder_date < datetime.utcnow():
                return jsonify({'error': 'La fecha de recordatorio debe ser futura'}), 400
        except Exception:
            return jsonify({'error': 'Formato de fecha de recordatorio inválido'}), 400
    list_item = List.query.get_or_404(data['list_id'])
    board = db.session.get(Board, list_item.board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    # Obtener la posición máxima
    max_position = db.session.query(db.func.max(Card.position)).filter_by(list_id=data['list_id']).scalar() or 0
    attachment_path = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        attachment_path = f"uploads/{unique_filename}"
    card = Card(
        title=data['title'],
        description=data.get('description', ''),
        list_id=data['list_id'],
        creator_id=current_user.id,
        position=max_position + 1,
        priority=data.get('priority', 'medium'),
        label_id=data.get('label_id'),
        attachment=attachment_path
    )
    if data.get('due_date'):
        card.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    if data.get('reminder_date'):
        card.reminder_date = datetime.fromisoformat(data['reminder_date'].replace('Z', '+00:00'))
    db.session.add(card)
    db.session.commit()
    
    # Preparar respuesta inmediata
    response_data = {
        'id': card.id,
        'title': card.title,
        'description': card.description,
        'position': card.position,
        'priority': card.priority,
        'label_id': card.label_id,
        'due_date': card.due_date.isoformat() if card.due_date else None,
        'reminder_date': card.reminder_date.isoformat() if card.reminder_date else None,
        'attachment': card.attachment
    }
    
    # Enviar email y registrar actividad de forma asíncrona
    def background_tasks():
        try:
            with app.app_context():
                # Enviar email si hay fecha de vencimiento
                if card.due_date:
                    send_card_notification(card)
                
                # Registrar actividad
                log = ActivityLog(
                    user_id=current_user.id, 
                    board_id=board.id, 
                    details=f"Crear tarjeta: Título: {data['title']}"
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            print(f"Error in background tasks: {e}")
    
    # Ejecutar tareas en background
    thread = threading.Thread(target=background_tasks)
    thread.daemon = True
    thread.start()
    
    return jsonify(response_data)

@app.route('/api/card/<int:card_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
@login_required
def manage_card(card_id):
    card = Card.query.get_or_404(card_id)
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    if request.method == 'DELETE':
        db.session.delete(card)
        db.session.commit()
        # Registrar actividad
        log_activity_async(current_user.id, board.id, 'Eliminar tarjeta', f'Título: {card.title}')
        return jsonify({'message': 'Tarjeta eliminada'})
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form
        file = request.files.get('attachment')
    else:
        data = request.get_json()
        file = None
    card.title = data['title']
    card.description = data.get('description', '')
    card.priority = data.get('priority', 'medium')
    card.label_id = data.get('label_id')
    if data.get('due_date'):
        card.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    else:
        card.due_date = None
    if data.get('reminder_date'):
        card.reminder_date = datetime.fromisoformat(data['reminder_date'].replace('Z', '+00:00'))
    else:
        card.reminder_date = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        card.attachment = f"uploads/{unique_filename}"
    db.session.commit()
    # Enviar email si hay fecha de vencimiento
    if card.due_date:
        send_card_notification(card)
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Actualizar tarjeta', f'Título: {data["title"]}')
    return jsonify({
        'id': card.id,
        'title': card.title,
        'description': card.description,
        'priority': card.priority,
        'label_id': card.label_id,
        'due_date': card.due_date.isoformat() if card.due_date else None,
        'reminder_date': card.reminder_date.isoformat() if card.reminder_date else None,
        'attachment': card.attachment
    })

@app.route('/api/card/<int:card_id>/move', methods=['POST'])
@csrf.exempt
@login_required
def move_card(card_id):
    data = request.get_json()
    card = Card.query.get_or_404(card_id)
    new_list_id = data['list_id']
    new_position = data['position']
    
    # Verificar permisos
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    
    # Actualizar posición de otras tarjetas en la lista origen
    if card.list_id != new_list_id:
        cards_in_old_list = Card.query.filter_by(list_id=card.list_id).filter(Card.position > card.position).all()
        for c in cards_in_old_list:
            c.position -= 1
    
    # Actualizar posición de otras tarjetas en la lista destino
    cards_in_new_list = Card.query.filter_by(list_id=new_list_id).filter(Card.position >= new_position).all()
    for c in cards_in_new_list:
        c.position += 1
    
    card.list_id = new_list_id
    card.position = new_position
    db.session.commit()
    
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Mover tarjeta', f'De: {card.list.title}, A: {list_item.title}')
    
    return jsonify({'message': 'Tarjeta movida'})

@app.route('/api/board/<int:board_id>/invite', methods=['POST'])
@csrf.exempt
@login_required
def invite_user(board_id):
    data = request.get_json()
    board = Board.query.get_or_404(board_id)
    
    if board.owner_id != current_user.id:
        return jsonify({'error': 'Solo el propietario puede invitar usuarios'}), 403
    
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    if user.id == current_user.id:
        return jsonify({'error': 'No puedes invitarte a ti mismo'}), 400
    
    existing_membership = BoardMember.query.filter_by(board_id=board_id, user_id=user.id).first()
    if existing_membership:
        return jsonify({'error': 'El usuario ya es miembro del tablero'}), 400
    
    can_edit = data.get('can_edit', True)  # Por defecto puede editar
    membership = BoardMember(board_id=board_id, user_id=user.id, role='member', can_edit=can_edit)
    db.session.add(membership)
    db.session.commit()
    
    # Enviar email de invitación
    send_invitation_email(user, board)
    
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Invitar usuario', f'Email: {data["email"]}')
    
    return jsonify({'message': 'Usuario invitado exitosamente'})

# API Routes para Checklists
@app.route('/api/card/<int:card_id>/checklist', methods=['POST'])
@csrf.exempt
@login_required
def add_checklist_item(card_id):
    data = request.get_json()
    card = Card.query.get_or_404(card_id)
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    
    # Obtener la posición máxima
    max_position = db.session.query(db.func.max(ChecklistItem.position)).filter_by(card_id=card_id).scalar() or 0
    
    item = ChecklistItem(
        text=data['text'],
        card_id=card_id,
        position=max_position + 1
    )
    
    db.session.add(item)
    db.session.commit()
    
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Crear checklist', f'Título: {data["text"]}')
    
    return jsonify({
        'id': item.id,
        'text': item.text,
        'completed': item.completed,
        'position': item.position
    })

@app.route('/api/checklist/<int:item_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
@login_required
def manage_checklist_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    card = Card.query.get(item.card_id)
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        # Registrar actividad
        log_activity_async(current_user.id, board.id, 'Eliminar checklist', f'Título: {item.text}')
        return jsonify({'message': 'Item eliminado'})
    
    data = request.get_json()
    item.text = data.get('text', item.text)
    item.completed = data.get('completed', item.completed)
    db.session.commit()
    
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Actualizar checklist', f'Título: {data["text"]}')
    
    return jsonify({
        'id': item.id,
        'text': item.text,
        'completed': item.completed,
        'position': item.position
    })

# API Routes para Comentarios
@app.route('/api/card/<int:card_id>/comment', methods=['POST'])
@csrf.exempt
@login_required
def add_comment(card_id):
    data = request.get_json()
    card = Card.query.get_or_404(card_id)
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership:
            return jsonify({'error': 'No tienes permisos'}), 403
    comment = Comment(
        text=data['text'],
        card_id=card_id,
        user_id=current_user.id,
        parent_id=data.get('parent_id')
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'id': comment.id,
        'text': comment.text,
        'user': {
            'id': comment.user.id,
            'username': comment.user.username
        },
        'created_at': comment.created_at.isoformat(),
        'parent_id': comment.parent_id
    })

@app.route('/api/card/<int:card_id>/comments', methods=['GET'])
@login_required
def get_comments(card_id):
    card = Card.query.get_or_404(card_id)
    # Obtener todos los comentarios de la tarjeta
    comments = Comment.query.filter_by(card_id=card_id).order_by(Comment.created_at).all()
    # Convertir a árbol
    def build_tree(comments, parent=None):
        tree = []
        for c in comments:
            if c.parent_id == parent:
                node = {
                    'id': c.id,
                    'text': c.text,
                    'user': {'id': c.user.id, 'username': c.user.username},
                    'created_at': c.created_at.isoformat(),
                    'parent_id': c.parent_id,
                    'replies': build_tree(comments, c.id)
                }
                tree.append(node)
        return tree
    return jsonify(build_tree(comments))

@app.route('/api/comment/<int:comment_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    card = Card.query.get(comment.card_id)
    list_item = List.query.get(card.list_id)
    board = db.session.get(Board, list_item.board_id)
    
    # Verificar permisos (solo el autor puede eliminar)
    if comment.user_id != current_user.id and board.owner_id != current_user.id:
        return jsonify({'error': 'No tienes permisos'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Eliminar comentario', f'Título: {card.title}')
    
    return jsonify({'message': 'Comentario eliminado'})

@app.route('/api/board/<int:board_id>/lists/reorder', methods=['POST'])
@csrf.exempt
@login_required
def reorder_lists(board_id):
    board = Board.query.get_or_404(board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    data = request.get_json()
    order = data.get('order', [])
    if not isinstance(order, list):
        return jsonify({'error': 'Formato de orden inválido'}), 400
    # Actualizar la posición de cada lista
    for idx, list_id in enumerate(order, start=1):
        list_item = List.query.filter_by(id=list_id, board_id=board_id).first()
        if list_item:
            list_item.position = idx
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Reordenar listas')
    return jsonify({'message': 'Orden actualizado'})

@app.route('/api/board/<int:board_id>/labels', methods=['GET'])
@login_required
def get_labels(board_id):
    board = Board.query.get_or_404(board_id)
    # Verificar permisos de acceso
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership:
            return jsonify({'error': 'No tienes permisos'}), 403
    labels = Label.query.filter_by(board_id=board_id).all()
    return jsonify([{'id': l.id, 'name': l.name, 'color': l.color} for l in labels])

@app.route('/api/board/<int:board_id>/labels', methods=['POST'])
@csrf.exempt
@login_required
def create_label(board_id):
    board = Board.query.get_or_404(board_id)
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    data = request.get_json()
    label = Label(name=data['name'], color=data.get('color', '#667eea'), board_id=board_id)
    db.session.add(label)
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Crear etiqueta', f'Título: {data["name"]}')
    return jsonify({'id': label.id, 'name': label.name, 'color': label.color})

@app.route('/api/label/<int:label_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_label(label_id):
    label = Label.query.get_or_404(label_id)
    board = Board.query.get(label.board_id)
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    if request.method == 'DELETE':
        db.session.delete(label)
        db.session.commit()
        # Registrar actividad
        log_activity_async(current_user.id, board.id, 'Eliminar etiqueta', f'Título: {label.name}')
        return jsonify({'message': 'Etiqueta eliminada'})
    data = request.get_json()
    label.name = data['name']
    label.color = data.get('color', label.color)
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Actualizar etiqueta', f'Título: {data["name"]}')
    return jsonify({'id': label.id, 'name': label.name, 'color': label.color})

@app.route('/api/card/<int:card_id>/assign', methods=['POST'])
@login_required
def assign_user_to_card(card_id):
    card = Card.query.get_or_404(card_id)
    list_item = List.query.get(card.list_id)
    board = Board.query.get(list_item.board_id)
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    data = request.get_json()
    user_id = data.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    # Solo miembros del tablero pueden ser asignados
    is_member = BoardMember.query.filter_by(board_id=board.id, user_id=user_id).first()
    if not is_member and board.owner_id != user_id:
        return jsonify({'error': 'El usuario no es miembro del tablero'}), 400
    card.assignee_id = user_id
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Asignar tarjeta', f'Usuario: {user.username}')
    return jsonify({'message': 'Usuario asignado', 'assignee': {'id': user.id, 'username': user.username}})

@app.route('/api/card/<int:card_id>/unassign', methods=['POST'])
@login_required
def unassign_user_from_card(card_id):
    card = Card.query.get_or_404(card_id)
    list_item = List.query.get(card.list_id)
    board = Board.query.get(list_item.board_id)
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board.id, user_id=current_user.id).first()
        if not membership or not membership.can_edit:
            return jsonify({'error': 'No tienes permisos'}), 403
    card.assignee_id = None
    db.session.commit()
    # Registrar actividad
    log_activity_async(current_user.id, board.id, 'Desasignar tarjeta')
    return jsonify({'message': 'Usuario desasignado'})

def send_card_notification(card):
    """Enviar notificación por email cuando se crea o actualiza una tarjeta con fecha de vencimiento"""
    try:
        msg = Message(
            f'Nueva tarjeta en Scotto: {card.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[card.creator.email]
        )
        msg.body = f'''
        Se ha creado/actualizado una tarjeta en Scotto:
        
        Título: {card.title}
        Descripción: {card.description or 'Sin descripción'}
        Fecha de vencimiento: {card.due_date.strftime('%d/%m/%Y %H:%M') if card.due_date else 'Sin fecha'}
        Prioridad: {card.priority}
        Lista: {card.list.title}
        Tablero: {card.list.board.title}
        
        ¡No olvides completar tu tarea!
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Error enviando email: {e}")

def send_invitation_email(user, board):
    """Enviar email de invitación a un tablero"""
    try:
        msg = Message(
            f'Invitación a tablero en Scotto: {board.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        msg.body = f'''
        Has sido invitado a unirse al tablero "{board.title}" en Scotto.
        
        Descripción: {board.description or 'Sin descripción'}
        Propietario: {board.owner.username}
        
        Inicia sesión en Scotto para acceder al tablero.
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Error enviando email de invitación: {e}")

def send_welcome_email(user):
    """Enviar email de bienvenida al usuario después del registro exitoso"""
    try:
        msg = Message(
            f'Bienvenido a Scotto: {user.username}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        msg.body = f'''
        ¡Bienvenido a Scotto!
        
        Gracias por registrarte.
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Error enviando email de bienvenida: {e}")

def send_reminder_email(card):
    """Enviar email de recordatorio cuando llega la fecha de recordatorio de una tarjeta"""
    try:
        destinatario = card.assignee.email if card.assignee else card.creator.email
        msg = Message(
            f'Recordatorio de tarjeta en Scotto: {card.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[destinatario]
        )
        msg.body = f'''
        ¡Tienes un recordatorio en Scotto!

        Título: {card.title}
        Descripción: {card.description or 'Sin descripción'}
        Fecha de recordatorio: {card.reminder_date.strftime('%d/%m/%Y %H:%M') if card.reminder_date else 'Sin fecha'}
        Prioridad: {card.priority}
        Lista: {card.list.title}
        Tablero: {card.list.board.title}
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Error enviando email de recordatorio: {e}")

@app.route('/api/send_reminders')
def send_reminders():
    now = datetime.utcnow()
    cards = Card.query.filter(Card.reminder_date.isnot(None), Card.reminder_date <= now).all()
    count = 0
    for card in cards:
        send_reminder_email(card)
        # Para evitar enviar múltiples veces, borra la fecha de recordatorio
        card.reminder_date = None
        count += 1
    db.session.commit()
    return jsonify({'reminders_sent': count})

# Función para registrar actividad (optimizada)
def log_activity(user_id, board_id, action, details=None):
    # Combinar action y details en el campo details
    full_details = f"{action}: {details}" if details else action
    log = ActivityLog(user_id=user_id, board_id=board_id, details=full_details)
    db.session.add(log)
    # No hacer commit aquí, se hará después
    return log

# Función para registrar actividad de forma asíncrona
def log_activity_async(user_id, board_id, action, details=None):
    try:
        log = log_activity(user_id, board_id, action, details)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {e}")

@app.route('/api/search')
@login_required
def global_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'boards': [], 'lists': [], 'cards': []})
    # Buscar tableros
    boards = Board.query.filter(Board.title.ilike(f'%{q}%')).all()
    # Buscar listas
    lists = List.query.filter(List.title.ilike(f'%{q}%')).all()
    # Buscar tarjetas
    cards = Card.query.filter((Card.title.ilike(f'%{q}%')) | (Card.description.ilike(f'%{q}%'))).all()
    return jsonify({
        'boards': [{'id': b.id, 'title': b.title} for b in boards],
        'lists': [{'id': l.id, 'title': l.title, 'board_id': l.board_id} for l in lists],
        'cards': [{'id': c.id, 'title': c.title, 'description': c.description, 'list_id': c.list_id} for c in cards]
    })

swagger = Swagger(app)

@app.route('/api/board/<int:board_id>/export/json')
@login_required
def export_board_json(board_id):
    board = Board.query.get_or_404(board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership:
            return jsonify({'error': 'No tienes permisos'}), 403
    data = {
        'id': board.id,
        'title': board.title,
        'description': board.description,
        'lists': []
    }
    for l in board.lists:
        list_data = {
            'id': l.id,
            'title': l.title,
            'cards': []
        }
        for c in l.cards:
            list_data['cards'].append({
                'id': c.id,
                'title': c.title,
                'description': c.description,
                'due_date': c.due_date.isoformat() if c.due_date else None,
                'reminder_date': c.reminder_date.isoformat() if c.reminder_date else None,
                'priority': c.priority,
                'label_id': c.label_id,
                'assignee_id': c.assignee_id,
                'attachment': c.attachment
            })
        data['lists'].append(list_data)
    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=tablero_{board.id}.json'
    return response

@app.route('/api/board/<int:board_id>/export/ics')
@login_required
def export_board_ics(board_id):
    board = Board.query.get_or_404(board_id)
    # Verificar permisos
    if board.owner_id != current_user.id:
        membership = BoardMember.query.filter_by(board_id=board_id, user_id=current_user.id).first()
        if not membership:
            return jsonify({'error': 'No tienes permisos'}), 403
    ics = 'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Scotto//EN\n'
    for l in board.lists:
        for c in l.cards:
            if c.due_date:
                ics += 'BEGIN:VEVENT\n'
                ics += f'SUMMARY:{c.title}\n'
                ics += f'DESCRIPTION:{c.description or ""}\n'
                ics += f'DTSTART:{c.due_date.strftime("%Y%m%dT%H%M%SZ")}\n'
                ics += f'DTEND:{c.due_date.strftime("%Y%m%dT%H%M%SZ")}\n'
                ics += f'UID:scotto-{c.id}@scotto\n'
                ics += 'END:VEVENT\n'
    ics += 'END:VCALENDAR\n'
    response = make_response(ics)
    response.headers['Content-Type'] = 'text/calendar'
    response.headers['Content-Disposition'] = f'attachment; filename=tablero_{board.id}.ics'
    return response

@app.errorhandler(500)
def internal_error(error):
    import traceback
    print(traceback.format_exc())  # Log para depuración
    response = jsonify({'error': 'Error interno del servidor', 'message': str(error)})
    response.status_code = 500
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if not app.debug:
        handler = RotatingFileHandler('error.log', maxBytes=100000, backupCount=3)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    # Solo ejecutar en modo debug localmente
    if app.debug:
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 