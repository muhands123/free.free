from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    """تسجيل مستخدم جديد"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    language = data.get('language', 'ar')
    
    if not username or not email or not password:
        return jsonify({'error': 'جميع الحقول مطلوبة'}), 400
    
    # التحقق من عدم وجود المستخدم مسبقاً
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'اسم المستخدم موجود مسبقاً'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'البريد الإلكتروني موجود مسبقاً'}), 400
    
    # إنشاء المستخدم الجديد
    user = User(
        username=username,
        email=email,
        preferred_language=language
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # تسجيل الدخول تلقائياً
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({
        'message': 'تم إنشاء الحساب بنجاح',
        'user': user.to_dict()
    }), 201

@user_bp.route('/login', methods=['POST'])
def login():
    """تسجيل الدخول"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'اسم المستخدم وكلمة المرور مطلوبان'}), 400
    
    # البحث عن المستخدم
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
    
    # تسجيل الدخول
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({
        'message': 'تم تسجيل الدخول بنجاح',
        'user': user.to_dict()
    })

@user_bp.route('/logout', methods=['POST'])
def logout():
    """تسجيل الخروج"""
    session.clear()
    return jsonify({'message': 'تم تسجيل الخروج بنجاح'})

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """الحصول على بيانات المستخدم الحالي"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'المستخدم غير موجود'}), 404
    
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    """تحديث بيانات المستخدم الحالي"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'المستخدم غير موجود'}), 404
    
    data = request.get_json()
    
    # تحديث البيانات
    if 'email' in data:
        email = data['email'].strip()
        if email and email != user.email:
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'البريد الإلكتروني موجود مسبقاً'}), 400
            user.email = email
    
    if 'preferred_language' in data:
        user.preferred_language = data['preferred_language']
    
    if 'password' in data and data['password'].strip():
        user.set_password(data['password'].strip())
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث البيانات بنجاح',
        'user': user.to_dict()
    })

@user_bp.route('/users', methods=['GET'])
def get_users():
    """الحصول على قائمة المستخدمين (للمدير فقط)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    current_user = User.query.get(user_id)
    if not current_user or not current_user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """الحصول على بيانات مستخدم محدد"""
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    # يمكن للمستخدم رؤية بياناته أو للمدير رؤية بيانات أي مستخدم
    if current_user_id != user_id:
        current_user = User.query.get(current_user_id)
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """حذف مستخدم (للمدير فقط)"""
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # منع المدير من حذف نفسه
    if user.id == current_user.id:
        return jsonify({'error': 'لا يمكنك حذف حسابك الخاص'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المستخدم بنجاح'})
