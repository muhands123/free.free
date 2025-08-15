from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Post, Comment, UserImage, DailyPoints, Tool
from datetime import datetime, timedelta
import os

admin_bp = Blueprint('admin', __name__)

def get_current_admin():
    """التحقق من أن المستخدم الحالي مدير"""
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user and user.is_admin:
            return user
    return None

@admin_bp.route('/admin/dashboard', methods=['GET'])
def get_dashboard_stats():
    """الحصول على إحصائيات لوحة التحكم"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    # إحصائيات عامة
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()
    pending_images = UserImage.query.filter_by(is_approved=False, is_active=True).count()
    
    # إحصائيات الأسبوع الماضي
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_comments_week = Comment.query.filter(Comment.created_at >= week_ago).count()
    
    # أكثر المستخدمين نشاطاً
    top_users = User.query.order_by(User.total_points.desc()).limit(5).all()
    
    # النقاط المكتسبة اليوم
    today = datetime.utcnow().date()
    points_today = db.session.query(db.func.sum(DailyPoints.points_earned)).filter(
        DailyPoints.date_earned == today
    ).scalar() or 0
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'total_posts': total_posts,
            'total_comments': total_comments,
            'pending_images': pending_images,
            'new_users_week': new_users_week,
            'new_comments_week': new_comments_week,
            'points_today': points_today
        },
        'top_users': [user.to_dict() for user in top_users]
    })

@admin_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    """الحصول على جميع المستخدمين"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    })

@admin_bp.route('/admin/users/<int:user_id>/toggle-admin', methods=['PUT'])
def toggle_user_admin(user_id):
    """تبديل صلاحيات المدير للمستخدم"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # منع المدير من إزالة صلاحياته الخاصة
    if user.id == admin.id:
        return jsonify({'error': 'لا يمكنك تعديل صلاحياتك الخاصة'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'message': f'تم {"منح" if user.is_admin else "إزالة"} صلاحيات المدير للمستخدم',
        'user': user.to_dict()
    })

@admin_bp.route('/admin/users/<int:user_id>/points', methods=['PUT'])
def update_user_points(user_id):
    """تحديث نقاط المستخدم"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    new_points = data.get('points')
    if new_points is None or new_points < 0:
        return jsonify({'error': 'عدد النقاط غير صحيح'}), 400
    
    user.total_points = new_points
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث نقاط المستخدم بنجاح',
        'user': user.to_dict()
    })

@admin_bp.route('/admin/images', methods=['GET'])
def get_pending_images():
    """الحصول على الصور في انتظار الموافقة"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', 'pending')  # pending, approved, all
    
    query = UserImage.query.filter_by(is_active=True)
    
    if status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    
    images = query.order_by(UserImage.upload_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'images': [image.to_dict() for image in images.items],
        'total': images.total,
        'pages': images.pages,
        'current_page': page
    })

@admin_bp.route('/admin/images/<int:image_id>/approve', methods=['PUT'])
def approve_image(image_id):
    """الموافقة على صورة"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    image = UserImage.query.get_or_404(image_id)
    image.is_approved = True
    db.session.commit()
    
    return jsonify({
        'message': 'تم الموافقة على الصورة',
        'image': image.to_dict()
    })

@admin_bp.route('/admin/images/<int:image_id>/reject', methods=['DELETE'])
def reject_image(image_id):
    """رفض ونذف صورة"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    image = UserImage.query.get_or_404(image_id)
    
    # حذف الملف من النظام
    if os.path.exists(image.image_path):
        try:
            os.remove(image.image_path)
        except:
            pass
    
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'message': 'تم رفض وحذف الصورة'})

@admin_bp.route('/admin/tools', methods=['GET'])
def get_tools_admin():
    """الحصول على جميع الأدوات للإدارة"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    tools = Tool.query.all()
    return jsonify([tool.to_dict() for tool in tools])

@admin_bp.route('/admin/tools/<int:tool_id>', methods=['PUT'])
def update_tool(tool_id):
    """تحديث إعدادات أداة"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json()
    
    # تحديث البيانات
    if 'name_ar' in data:
        tool.name_ar = data['name_ar'].strip()
    if 'name_en' in data:
        tool.name_en = data['name_en'].strip()
    if 'description_ar' in data:
        tool.description_ar = data['description_ar'].strip()
    if 'description_en' in data:
        tool.description_en = data['description_en'].strip()
    if 'is_active' in data:
        tool.is_active = data['is_active']
    if 'required_points' in data:
        tool.required_points = max(0, data['required_points'])
    if 'daily_points_reward' in data:
        tool.daily_points_reward = max(0, data['daily_points_reward'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'تم تحديث الأداة بنجاح',
        'tool': tool.to_dict()
    })

@admin_bp.route('/admin/analytics', methods=['GET'])
def get_analytics():
    """الحصول على تحليلات الموقع"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    # تحليل النقاط حسب الأداة
    tools_usage = db.session.query(
        DailyPoints.tool_name,
        db.func.count(DailyPoints.id).label('usage_count'),
        db.func.sum(DailyPoints.points_earned).label('total_points')
    ).group_by(DailyPoints.tool_name).all()
    
    # تحليل المستخدمين الجدد حسب الأسبوع
    weeks_data = []
    for i in range(4):  # آخر 4 أسابيع
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        
        new_users = User.query.filter(
            User.created_at >= week_start,
            User.created_at < week_end
        ).count()
        
        weeks_data.append({
            'week': f'الأسبوع {i+1}',
            'new_users': new_users
        })
    
    return jsonify({
        'tools_usage': [
            {
                'tool_name': usage.tool_name,
                'usage_count': usage.usage_count,
                'total_points': usage.total_points
            }
            for usage in tools_usage
        ],
        'weekly_users': weeks_data
    })

@admin_bp.route('/admin/cleanup', methods=['POST'])
def cleanup_expired_data():
    """تنظيف البيانات المنتهية الصلاحية"""
    admin = get_current_admin()
    if not admin:
        return jsonify({'error': 'غير مصرح لك بالوصول'}), 403
    
    now = datetime.utcnow()
    
    # حذف الصور المنتهية الصلاحية
    expired_images = UserImage.query.filter(UserImage.expiry_date < now).all()
    
    deleted_count = 0
    for image in expired_images:
        # حذف الملف من النظام
        if os.path.exists(image.image_path):
            try:
                os.remove(image.image_path)
                deleted_count += 1
            except:
                pass
        
        db.session.delete(image)
    
    db.session.commit()
    
    return jsonify({
        'message': f'تم حذف {deleted_count} صورة منتهية الصلاحية',
        'deleted_count': deleted_count
    })

