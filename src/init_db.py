from src.models.user import db, User, Tool, Post
from datetime import datetime

def init_database():
    """إعداد البيانات الأولية للتطبيق"""
    
    # التحقق من وجود المستخدم الإداري
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@smarttools.com',
            is_admin=True,
            total_points=1000,
            preferred_language='ar'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    # إعداد الأدوات الأساسية
    tools_data = [
        {
            'name': 'smart_titles',
            'name_ar': 'أداة العناوين الذكية',
            'name_en': 'Smart Titles Tool',
            'description_ar': 'أداة لإنشاء عناوين ذكية وجذابة لمحتواك',
            'description_en': 'Tool for creating smart and attractive titles for your content',
            'is_free': True,
            'required_points': 0,
            'daily_points_reward': 25
        },
        {
            'name': 'tasks',
            'name_ar': 'أداة المهام',
            'name_en': 'Tasks Tool',
            'description_ar': 'أداة لإدارة وتتبع مهامك اليومية',
            'description_en': 'Tool for managing and tracking your daily tasks',
            'is_free': True,
            'required_points': 0,
            'daily_points_reward': 25
        },
        {
            'name': 'smart_emoji',
            'name_ar': 'أداة الإيموجي الذكية',
            'name_en': 'Smart Emoji Tool',
            'description_ar': 'أداة لإنشاء واختيار الإيموجي المناسب لمحتواك',
            'description_en': 'Tool for creating and selecting appropriate emojis for your content',
            'is_free': True,
            'required_points': 0,
            'daily_points_reward': 25
        },
        {
            'name': 'advanced_titles',
            'name_ar': 'أداة العناوين المطورة',
            'name_en': 'Advanced Titles Tool',
            'description_ar': 'أداة متقدمة لإنشاء عناوين احترافية ومتطورة',
            'description_en': 'Advanced tool for creating professional and sophisticated titles',
            'is_free': False,
            'required_points': 200,
            'daily_points_reward': 0
        },
        {
            'name': 'user_image',
            'name_ar': 'أداة عرض الصورة',
            'name_en': 'User Image Display Tool',
            'description_ar': 'أداة لعرض صورتك في الموقع لمدة يوم واحد',
            'description_en': 'Tool to display your image on the website for one day',
            'is_free': False,
            'required_points': 500,
            'daily_points_reward': 0
        }
    ]
    
    for tool_data in tools_data:
        existing_tool = Tool.query.filter_by(name=tool_data['name']).first()
        if not existing_tool:
            tool = Tool(**tool_data)
            db.session.add(tool)
    
    # إنشاء منشورات تجريبية
    sample_posts = [
        {
            'title_ar': 'مرحباً بكم في موقع الأدوات الذكية',
            'title_en': 'Welcome to Smart Tools Website',
            'content_ar': 'نحن سعداء لانضمامكم إلى موقعنا الجديد للأدوات الذكية. هنا ستجدون مجموعة متنوعة من الأدوات المفيدة التي ستساعدكم في أعمالكم اليومية.',
            'content_en': 'We are happy to have you join our new smart tools website. Here you will find a variety of useful tools that will help you in your daily work.'
        },
        {
            'title_ar': 'كيفية كسب النقاط واستخدام الأدوات المتقدمة',
            'title_en': 'How to Earn Points and Use Advanced Tools',
            'content_ar': 'يمكنكم كسب 25 نقطة يومياً من كل أداة مجانية. عند الوصول إلى 200 نقطة، ستفتح لكم أداة العناوين المطورة، وعند 500 نقطة يمكنكم عرض صورتكم في الموقع.',
            'content_en': 'You can earn 25 points daily from each free tool. When you reach 200 points, the advanced titles tool will unlock, and at 500 points you can display your image on the website.'
        },
        {
            'title_ar': 'نصائح لاستخدام الأدوات بفعالية',
            'title_en': 'Tips for Using Tools Effectively',
            'content_ar': 'للحصول على أفضل النتائج من أدواتنا، ننصحكم بالاستخدام المنتظم والتفاعل مع المجتمع من خلال التعليقات.',
            'content_en': 'To get the best results from our tools, we recommend regular use and community interaction through comments.'
        }
    ]
    
    for post_data in sample_posts:
        existing_post = Post.query.filter_by(title_ar=post_data['title_ar']).first()
        if not existing_post:
            post = Post(**post_data)
            db.session.add(post)
    
    try:
        db.session.commit()
        print("تم إعداد البيانات الأولية بنجاح")
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في إعداد البيانات الأولية: {e}")

