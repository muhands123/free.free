from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Tool, DailyPoints, Task
from datetime import date, datetime
import random

tools_bp = Blueprint('tools', __name__)

def get_current_user():
    """الحصول على المستخدم الحالي من الجلسة"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def can_earn_points(user_id, tool_name):
    """التحقق من إمكانية كسب النقاط لأداة معينة اليوم"""
    today = date.today()
    existing_points = DailyPoints.query.filter_by(
        user_id=user_id,
        tool_name=tool_name,
        date_earned=today
    ).first()
    return existing_points is None

def award_points(user_id, tool_name, points=25):
    """منح النقاط للمستخدم"""
    if can_earn_points(user_id, tool_name):
        daily_points = DailyPoints(
            user_id=user_id,
            tool_name=tool_name,
            points_earned=points
        )
        db.session.add(daily_points)
        
        user = User.query.get(user_id)
        user.total_points += points
        db.session.commit()
        return True
    return False

@tools_bp.route('/tools', methods=['GET'])
def get_tools():
    """الحصول على قائمة الأدوات المتاحة"""
    tools = Tool.query.filter_by(is_active=True).all()
    user = get_current_user()
    
    tools_data = []
    for tool in tools:
        tool_dict = tool.to_dict()
        if user:
            tool_dict['can_use'] = (tool.is_free or 
                                  (tool.name == 'advanced_titles' and user.can_use_advanced_titles()) or
                                  (tool.name == 'user_image' and user.can_use_image_feature()))
            tool_dict['can_earn_points'] = can_earn_points(user.id, tool.name) if tool.is_free else False
        else:
            tool_dict['can_use'] = tool.is_free
            tool_dict['can_earn_points'] = False
        
        tools_data.append(tool_dict)
    
    return jsonify(tools_data)

@tools_bp.route('/tools/smart-titles', methods=['POST'])
def generate_smart_titles():
    """أداة إنشاء العناوين الذكية"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    data = request.get_json()
    topic = data.get('topic', '')
    language = data.get('language', user.preferred_language)
    
    if not topic:
        return jsonify({'error': 'يرجى إدخال الموضوع'}), 400
    
    # عناوين تجريبية (سيتم استبدالها بـ OpenAI لاحقاً)
    sample_titles_ar = [
        f"🚀 {topic}: دليلك الشامل للنجاح",
        f"💡 أسرار {topic} التي لم تعرفها من قبل",
        f"🔥 كيف تتقن {topic} في 7 خطوات بسيطة",
        f"⭐ {topic}: الطريق إلى الاحتراف",
        f"🎯 تعلم {topic} واحصل على النتائج المذهلة"
    ]
    
    sample_titles_en = [
        f"🚀 {topic}: Your Complete Guide to Success",
        f"💡 {topic} Secrets You Never Knew Before",
        f"🔥 Master {topic} in 7 Simple Steps",
        f"⭐ {topic}: The Path to Professionalism",
        f"🎯 Learn {topic} and Get Amazing Results"
    ]
    
    titles = sample_titles_ar if language == 'ar' else sample_titles_en
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
    
    # منح النقاط إذا كان ممكناً
    points_awarded = award_points(user.id, 'smart_titles')
    
    return jsonify({
        'titles': titles_text,
        'points_awarded': points_awarded,
        'user_points': user.total_points
    })

@tools_bp.route('/tools/advanced-titles', methods=['POST'])
def generate_advanced_titles():
    """أداة العناوين المطورة (تتطلب 200 نقطة)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    if not user.can_use_advanced_titles():
        return jsonify({'error': 'تحتاج إلى 200 نقطة لاستخدام هذه الأداة'}), 403
    
    data = request.get_json()
    topic = data.get('topic', '')
    style = data.get('style', 'professional')
    language = data.get('language', user.preferred_language)
    
    if not topic:
        return jsonify({'error': 'يرجى إدخال الموضوع'}), 400
    
    # عناوين متقدمة تجريبية
    advanced_titles_ar = [
        f"📊 تحليل شامل: {topic} وتأثيره على السوق (تقييم: 9/10)",
        f"🎓 دليل الخبراء: إتقان {topic} بمنهجية علمية (تقييم: 10/10)",
        f"💼 استراتيجية احترافية: {topic} للمؤسسات الناجحة (تقييم: 9/10)",
        f"🔬 دراسة متعمقة: {topic} والابتكار التقني (تقييم: 8/10)",
        f"📈 تطبيق عملي: {topic} لتحقيق النمو المستدام (تقييم: 9/10)"
    ]
    
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(advanced_titles_ar)])
    
    return jsonify({
        'titles': titles_text,
        'style': style,
        'user_points': user.total_points
    })

@tools_bp.route('/tools/smart-emoji', methods=['POST'])
def generate_smart_emoji():
    """أداة الإيموجي الذكية"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    data = request.get_json()
    text = data.get('text', '')
    mood = data.get('mood', 'neutral')
    
    if not text:
        return jsonify({'error': 'يرجى إدخال النص'}), 400
    
    # إيموجي تجريبية حسب المزاج
    emoji_sets = {
        'happy': ['😊', '😄', '🎉', '✨', '🌟', '💫', '🎊', '🥳'],
        'professional': ['💼', '📊', '📈', '🎯', '⭐', '🏆', '💡', '🔥'],
        'creative': ['🎨', '✨', '🌈', '💡', '🚀', '⚡', '🎭', '🎪'],
        'excited': ['🚀', '⚡', '🔥', '💥', '🎯', '🌟', '✨', '🎉'],
        'neutral': ['📝', '💭', '🤔', '📚', '💡', '🔍', '📌', '✅']
    }
    
    selected_emojis = emoji_sets.get(mood, emoji_sets['neutral'])
    random_emojis = random.sample(selected_emojis, min(5, len(selected_emojis)))
    
    emoji_suggestions = f"""الإيموجي المقترحة للنص: "{text[:50]}..."

الإيموجي المناسبة: {' '.join(random_emojis)}

تفسير الاختيار:
• هذه الإيموجي تناسب المزاج المطلوب ({mood})
• تعزز المعنى وتجعل النص أكثر تفاعلاً
• مناسبة لوسائل التواصل الاجتماعي

اقتراحات للاستخدام:
- ضع الإيموجي في بداية أو نهاية النص
- استخدم إيموجي واحد أو اثنين لتجنب الإفراط
- اختر الإيموجي الذي يناسب جمهورك المستهدف"""
    
    # منح النقاط إذا كان ممكناً
    points_awarded = award_points(user.id, 'smart_emoji')
    
    return jsonify({
        'emoji_suggestions': emoji_suggestions,
        'points_awarded': points_awarded,
        'user_points': user.total_points
    })

@tools_bp.route('/tasks', methods=['GET'])
def get_user_tasks():
    """الحصول على مهام المستخدم"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks])

@tools_bp.route('/tasks', methods=['POST'])
def create_task():
    """إنشاء مهمة جديدة"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    
    if not title:
        return jsonify({'error': 'يرجى إدخال عنوان المهمة'}), 400
    
    task = Task(
        user_id=user.id,
        title=title,
        description=description
    )
    
    db.session.add(task)
    db.session.commit()
    
    # منح النقاط إذا كان ممكناً
    points_awarded = award_points(user.id, 'tasks')
    
    return jsonify({
        'task': task.to_dict(),
        'points_awarded': points_awarded,
        'user_points': user.total_points
    })

@tools_bp.route('/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    """تمييز المهمة كمكتملة"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        return jsonify({'error': 'المهمة غير موجودة'}), 404
    
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(task.to_dict())

@tools_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """حذف مهمة"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        return jsonify({'error': 'المهمة غير موجودة'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'تم حذف المهمة بنجاح'})

@tools_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """الحصول على لوحة الصدارة (أفضل 10 مستخدمين)"""
    top_users = User.query.filter(User.total_points > 0).order_by(User.total_points.desc()).limit(10).all()
    
    leaderboard = []
    for i, user in enumerate(top_users, 1):
        leaderboard.append({
            'rank': i,
            'username': user.username,
            'total_points': user.total_points
        })
    
    return jsonify(leaderboard)

