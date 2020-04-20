from flask import Flask, render_template, redirect, request, abort, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from forms import LoginForm, RegisterForm, NewsForm, MessageForm
from data import db_session

from data.chats import Chat
from data.messages import Message
from data.news import News
from data.comments import Comment
from data.users import User
from data.friends import Friends
from data.friend_requests import FriendRequest

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'Pip123ininty321Subject'


@app.route('/chats/create')
@app.route('/chats/<int:chat_id>/edit')
@app.route('/chats/<int:chat_id>/delete')
@app.route('/chats/<int:chat_id>/delete_message/<int:message_id>')
@app.route('/me/edit')
@app.route('/news')
@login_required
def not_using(*args, **kwargs):
    return render_template('base.html', title='PLy.Chats')


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect('/news')
    return render_template('index.html', title='Welcome | PLy.Chats')


@app.route('/me')
@login_required
def me():
    return redirect(f'/{current_user.id}')


@app.route('/<int:id>')
def user_page(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    if user:
        return render_template('user_page.html', title=f'{user.surname} {user.name}', user=user,
                               session=session, FriendRequest=FriendRequest)
    else:
        abort(404)


@app.route('/friends')
@login_required
def list_friends():
    session = db_session.create_session()
    friends = current_user.get_all_friends_users(session)
    return render_template('friends.html', title='Друзья', friends=friends,
                           session=session, User=User)


@app.route('/friends/delete/<int:id>')
@login_required
def delete_friend(id):
    session = db_session.create_session()

    if current_user.is_friend(id, session):
        session.delete(current_user.get_obj_friends_with_user(id, session))
        session.commit()
        return redirect(f'/{id}')
    else:
        abort(404)


@app.route('/friends/requests')
@login_required
def list_friend_requests():
    session = db_session.create_session()
    friend_requests_in = session.query(FriendRequest).filter(FriendRequest.recipient == current_user.id).all()
    friend_requests_out = session.query(FriendRequest).filter(FriendRequest.sender == current_user.id).all()
    return render_template('friend_requests.html', title='Заявки в друзья', session=session, User=User,
                           requests_in=friend_requests_in, requests_out=friend_requests_out)


@app.route('/friends/requests/send/<int:id>')
@login_required
def send_friend_requests(id):
    session = db_session.create_session()

    if current_user.is_friend(id, session):
        return redirect(f'/{id}')

    # Если запрос уже бьл то отменить
    friend_request = session.query(FriendRequest).filter(FriendRequest.sender == current_user.id,
                                                         FriendRequest.recipient == id).first()
    if friend_request:
        return redirect(f'/{id}')

    # При взаимных запросах принять
    friend_request = session.query(FriendRequest).filter(FriendRequest.sender == id,
                                                         FriendRequest.recipient == current_user.id).first()
    if friend_request:
        return redirect(f'/friends/requests/accept/{friend_request.id}')

    friend_request = FriendRequest()
    friend_request.sender = current_user.id
    friend_request.recipient = id
    session.add(friend_request)
    session.commit()
    return redirect(f'/{id}')


@app.route('/friends/requests/accept/<int:id>')
@login_required
def accept_friend_request(id):
    session = db_session.create_session()
    friend_request = session.query(FriendRequest).filter(FriendRequest.id == id,
                                                         FriendRequest.recipient == current_user.id).first()
    if friend_request:
        friend = Friends(user_id_a=friend_request.sender, user_id_b=friend_request.recipient)
        session.add(friend)
        session.delete(friend_request)
        session.commit()
        return redirect('/friends/requests')
    else:
        abort(404)


@app.route('/friends/requests/delete/<int:id>')
@login_required
def delete_friend_requests(id):
    session = db_session.create_session()
    friend_request = session.query(FriendRequest).filter(FriendRequest.id == id,
                                                         (FriendRequest.sender == current_user.id) |
                                                         (FriendRequest.recipient == current_user.id)).first()
    if friend_request:
        session.delete(friend_request)
        session.commit()
        return redirect('/friends/requests')
    else:
        abort(404)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def view_news(id):
    form = MessageForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          (News.is_private == False) | (News.user == current_user)).first()
        if news:
            return render_template('view_news.html', title=f'{news.title}', news=news, form=form,
                                   session=session, User=User)
        else:
            abort(404)

    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          (News.is_private == False) | (News.user == current_user)).first()
        if news:
            comment = Comment(content=form.content.data, id=current_user.id)
            news.comments.append(comment)
            session.commit()
            return redirect(f'/news/{id}')
        else:
            abort(404)


@app.route('/news/add', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/me')
    return render_template('news.html', title='Добавление записи',
                           form=form)


@app.route('/news/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            session.commit()
            return redirect('/me')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/news/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_news(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      News.user == current_user).first()
    if news:
        for comment in news.comments:
            session.delete(comment)
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/me')


@app.route('/news/<int:news_id>/comments/delete/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def delete_comment(news_id, comment_id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == news_id).first()
    if news:
        comment = list(
            filter(lambda c: c.id == comment_id and (news.user == current_user or c.user_id == current_user.id),
                   news.comments))
        if comment:
            session.delete(comment[0])
            session.commit()
        else:
            abort(404)
    else:
        abort(404)
    return redirect(f'/news/{news_id}')


@app.route('/chats')
@login_required
def list_chats():
    session = db_session.create_session()
    chats = list(current_user.chats)
    return render_template('chats.html', title='Чаты', session=session, chats=chats)


@app.route('/chats/<int:id>', methods=['GET', 'POST'])
@login_required
def view_chat(id):
    form = MessageForm()
    if request.method == "GET":
        session = db_session.create_session()
        chat = list(filter(lambda x: x.id == id, current_user.chats))
        if chat:
            messages = session.query(Message).filter(Message.chat_id == id).all()
            return render_template('view_chat.html', title=chat[0].get_name(session, current_user), chat=chat[0],
                                   form=form,
                                   messages=messages, session=session, User=User)
        else:
            abort(404)

    if form.validate_on_submit():
        session = db_session.create_session()
        chat = list(filter(lambda x: x.id == id, current_user.chats))
        if chat:
            message = Message(content=form.content.data, user_id=current_user.id, chat_id=id)
            session.add(message)
            session.commit()
            return redirect(f'/chats/{id}')
        else:
            abort(404)


@app.route('/chats/<int:chat_id>/delete_message/<int:message_id>')
def delete_message(chat_id, message_id):
    session = db_session.create_session()
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        message = session.query(Message).filter(Message.id == message_id, Message.chat_id == chat_id,
                                                Message.user_id == current_user.id).first()
        if message:
            session.delete(message)
            session.commit()
            return redirect(f'/chats/{chat_id}')
        else:
            abort(404)
    else:
        abort(404)


@app.route('/chats/open_with_friend/<int:id>')
def open_chat_with_user(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    if not user or not user.is_friend(current_user.id, session):
        abort(404)
    for chat in current_user.chats:
        if any(map(lambda y: chat.id == y.id, user.chats)):
            session.close()
            return redirect(f'/chats/{chat.id}')
    # session.close()
    #
    # session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    chat = Chat(owner=current_user.id, is_public=False)
    current_user.chats.append(chat)
    user.chats.append(chat)
    session.add(chat)
    session.commit()
    session.close()
    return redirect(f'/chats/{chat.id}')


# @app.route('/chats/add/<user:id>')
# def p(*args, **kwargs): pass


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/news')
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой email уже занят")

        user = User()
        user.name = form.name.data
        user.surname = form.surname.data
        user.patronymic = form.patronymic.data
        user.email = form.email.data

        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init('db/db_social_network.sqlite')
    t()
    app.run(port=8080, host='127.0.0.1')


def t():
    session = db_session.create_session()
    user1: User = session.query(User).filter(User.id == 1).first()
    if not user1:
        user1 = User(name='Макс', surname='Sh', email='maxsika2004@mail.ru')
        user1.set_password('123')
        session.add(user1)
        session.commit()

    user2: User = session.query(User).filter(User.id == 2).first()
    if not user2:
        user2 = User(name='Паша', surname='Ла', email='pa@mail.ru')
        user2.set_password('123')
        session.add(user2)
    session.commit()

    user3: User = session.query(User).filter(User.id == 3).first()
    if not user3:
        user3 = User(name='Елена', surname='sh', email='e@mail.ru')
        user3.set_password('123')
        session.add(user3)
    session.commit()

    if not user1.is_friend(user2.id, session):
        friend = Friends(user_id_a=user1.id, user_id_b=user2.id)
        session.add(friend)
        session.commit()

    chat = session.query(Chat).filter(Chat.id == 1).first()
    if not chat:
        chat = Chat(owner=user1.id, is_public=False)
        user1.chats.append(chat)
        user2.chats.append(chat)
        message = Message(content=f'Сообщение {chat.id}', user_id=user1.id, chat_id=chat.id)
        session.add(message)
        session.commit()
    session.close()


if __name__ == "__main__":
    main()