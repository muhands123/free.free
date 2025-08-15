from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Post, Comment
from datetime import datetime

posts_bp = Blueprint('posts', __name__)

def get_current_user():
    """الحصول على المستخدم الحالي من الجلسة"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@posts_bp.route('/posts', methods=['GET'])
def get_posts():
    """الحصول على قائمة المنشورات"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = Post.query.filter_by(is_active=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [post.to_dict() for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page
    })

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """الحصول على منشور محدد"""
    post = Post.query.filter_by(id=post_id, is_active=True).first_or_404()
    return jsonify(post.to_dict())

@posts_bp.route('/posts', methods=['POST'])
def create_post():
    """إنشاء منشور جديد (للمدير فقط)"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    data = request.get_json()
    
    title_ar = data.get('title_ar', '').strip()
    title_en = data.get('title_en', '').strip()
    content_ar = data.get('content_ar', '').strip()
    content_en = data.get('content_en', '').strip()
    
    if not title_ar or not title_en or not content_ar or not content_en:
        return jsonify({'error': 'جميع الحقول مطلوبة'}), 400
    
    post = Post(
        title_ar=title_ar,
        title_en=title_en,
        content_ar=content_ar,
        content_en=content_en
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'message': 'تم إنشاء المنشور بنجاح',
        'post': post.to_dict()
    }), 201

@posts_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """تحديث منشور (للمدير فقط)"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    # تحديث البيانات
    if 'title_ar' in data:
        post.title_ar = data['title_ar'].strip()
    if 'title_en' in data:
        post.title_en = data['title_en'].strip()
    if 'content_ar' in data:
        post.content_ar = data['content_ar'].strip()
    if 'content_en' in data:
        post.content_en = data['content_en'].strip()
    if 'is_active' in data:
        post.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث المنشور بنجاح',
        'post': post.to_dict()
    })

@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """حذف منشور (للمدير فقط)"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المنشور بنجاح'})

@posts_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """الحصول على تعليقات منشور"""
    post = Post.query.filter_by(id=post_id, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    comments = Comment.query.filter_by(
        post_id=post_id, 
        is_approved=True
    ).order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'comments': [comment.to_dict() for comment in comments.items],
        'total': comments.total,
        'pages': comments.pages,
        'current_page': page
    })

@posts_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """إضافة تعليق على منشور"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    post = Post.query.filter_by(id=post_id, is_active=True).first_or_404()
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'محتوى التعليق مطلوب'}), 400
    
    if len(content) > 1000:
        return jsonify({'error': 'التعليق طويل جداً (الحد الأقصى 1000 حرف)'}), 400
    
    comment = Comment(
        content=content,
        user_id=user.id,
        post_id=post_id,
        is_approved=True  # الموافقة التلقائية، يمكن تغييرها لاحقاً
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'تم إضافة التعليق بنجاح',
        'comment': comment.to_dict()
    }), 201

@posts_bp.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    """تحديث تعليق (للمالك أو المدير)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    comment = Comment.query.get_or_404(comment_id)
    
    # التحقق من الصلاحيات
    if comment.user_id != user.id and not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بتعديل هذا التعليق'}), 403
    
    data = request.get_json()
    
    if 'content' in data and comment.user_id == user.id:
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'محتوى التعليق مطلوب'}), 400
        if len(content) > 1000:
            return jsonify({'error': 'التعليق طويل جداً (الحد الأقصى 1000 حرف)'}), 400
        comment.content = content
    
    if 'is_approved' in data and user.is_admin:
        comment.is_approved = data['is_approved']
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث التعليق بنجاح',
        'comment': comment.to_dict()
    })

@posts_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """حذف تعليق (للمالك أو المدير)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    comment = Comment.query.get_or_404(comment_id)
    
    # التحقق من الصلاحيات
    if comment.user_id != user.id and not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بحذف هذا التعليق'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف التعليق بنجاح'})

@posts_bp.route('/admin/comments', methods=['GET'])
def get_all_comments():
    """الحصول على جميع التعليقات (للمدير فقط)"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    approved_only = request.args.get('approved_only', 'false').lower() == 'true'
    
    query = Comment.query
    if approved_only:
        query = query.filter_by(is_approved=True)
    
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'comments': [comment.to_dict() for comment in comments.items],
        'total': comments.total,
        'pages': comments.pages,
        'current_page': page
    })

