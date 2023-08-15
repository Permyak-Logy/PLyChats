import sqlalchemy.exc
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from forms import LoginForm, RegisterForm, NewsForm, MessageForm, AccountForm
from data import db_session
from data import Chat, Message, News, Comment, User, Friends, FriendRequest

from datetime import datetime

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
# noinspection SpellCheckingInspection
app.config['SECRET_KEY'] = 'Pip123ininty321Subject'


@app.route('/me/delete')
@login_required
def delete_me(*_, **__):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    if user:
        for friend in user.get_all_friends_users(session):
            delete_friend(friend.id)
        for news in user.news:
            delete_news(news.id)
        session.close()
        # После удаления новостей и друзей, нужно ОБЯЗЯТЕЛЬНО пересоздать сессию и
        # сделать повторный поиск человека, иначе вылезет ОШИБКА
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        session.delete(user)
        session.commit()
        session.close()
    return redirect('/')


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect('/news')
    return render_template('index.html', title='Welcome | PLy.Chats')


@app.route('/me')
@login_required
def me():  # Перенаправит на свою страницу текущего пользователя
    return redirect(f'/{current_user.id}')


@app.route('/me/edit', methods=['GET', 'POST'])
@login_required
def edit_me():
    form = AccountForm()
    with db_session.create_session() as session:
        if request.method == "GET":
            user = session.query(User).filter(User.id == current_user.id).first()
            if user:
                form.name.data = user.name
                form.surname.data = user.surname
                form.patronymic.data = user.patronymic
                form.about.data = user.about
                form.email.data = user.email
                form.phone.data = user.phone
                form.address.data = user.address
            else:
                abort(404)
        if form.validate_on_submit():
            user = session.query(User).filter(User.id == current_user.id).first()
            if user:
                if session.query(User).filter(User.id != user.id, User.email == form.email.data).first():
                    return render_template('me.html', title='Аккаунт',
                                           form=form,
                                           message="Такой email уже занят")
                if session.query(User).filter(User.id != user.id, User.phone == form.phone.data).first():
                    return render_template('me.html', title='Аккаунт',
                                           form=form,
                                           message="Такой телефон уже занят")

                user.name = form.name.data
                user.surname = form.surname.data
                user.patronymic = form.patronymic.data
                user.about = form.about.data
                user.email = form.email.data
                user.phone = form.phone.data
                user.address = form.address.data
                user.modified_date = datetime.now()
                session.commit()
                return redirect('/me')
            else:
                abort(404)
    return render_template('me.html', title='Аккаунт', form=form)


@app.route('/<int:id>')
def user_page(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    if user:
        current_user_is_friend_user = current_user.is_friend(session, user.id)
        friend_request = session.query(FriendRequest).filter(FriendRequest.sender == current_user.id,
                                                             FriendRequest.recipient == user.id).first()
        news = list(filter(lambda x: not x.is_private or x.user == current_user, user.news))[::-1]

        session.close()
        return render_template('user_page.html', title=f'{user.surname} {user.name}', user=user, news=news,
                               current_user_is_friend_user=current_user_is_friend_user, friend_request=friend_request)
    else:
        abort(404)


@app.route('/friends')
@login_required
def list_friends():
    session = db_session.create_session()
    friends = current_user.get_all_friends_users(session)
    session.close()
    return render_template('friends.html', title='Друзья', friends=friends)


@app.route('/friends/delete/<int:id>')
@login_required
def delete_friend(id):
    session = db_session.create_session()

    if current_user.is_friend(session, id):
        chat = current_user.get_chat_with_user(session, id)
        session.delete(chat) if chat else None
        session.delete(current_user.get_obj_friends_with_user(session, id))
        session.commit()
        session.close()
        return redirect(f'/{id}')
    else:
        abort(404)


@app.route('/friends/requests')
@login_required
def list_friend_requests():
    session = db_session.create_session()
    friend_requests_in = session.query(FriendRequest).filter(FriendRequest.recipient == current_user.id).all()
    friend_requests_out = session.query(FriendRequest).filter(FriendRequest.sender == current_user.id).all()
    friend_requests_in_list_dict = [
        {
            'id': elem.id,
            'sender': session.query(User).filter(User.id == elem.sender).first(),
            'recipient': session.query(User).filter(User.id == elem.recipient).first()
        } for elem in friend_requests_in
    ]  # Входящие запросы в друзья
    friend_requests_out_list_dict = [
        {
            'id': elem.id,
            'sender': session.query(User).filter(User.id == elem.sender).first(),
            'recipient': session.query(User).filter(User.id == elem.recipient).first()
        } for elem in friend_requests_out
    ]  # Исходящие запросы в друзья
    session.close()
    return render_template('friend_requests.html', title='Заявки в друзья',
                           requests_in=friend_requests_in_list_dict, requests_out=friend_requests_out_list_dict)


@app.route('/friends/requests/send/<int:id>')
@login_required
def send_friend_requests(id):
    session = db_session.create_session()

    if current_user.is_friend(session, id):
        # Нельзя отправить приглашение в др если он и так друг
        session.close()
        return redirect(f'/{id}')

    # Если запрос уже бьл то отменить
    friend_request = session.query(FriendRequest).filter(FriendRequest.sender == current_user.id,
                                                         FriendRequest.recipient == id).first()
    if friend_request:
        session.close()
        return redirect(f'/{id}')

    # При взаимных запросах принять
    friend_request = session.query(FriendRequest).filter(FriendRequest.sender == id,
                                                         FriendRequest.recipient == current_user.id).first()
    if friend_request:
        session.close()
        return redirect(f'/friends/requests/accept/{friend_request.id}')

    friend_request = FriendRequest()
    friend_request.sender = current_user.id
    friend_request.recipient = id
    session.add(friend_request)
    session.commit()
    session.close()
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
        session.close()
        return redirect('/friends/requests')
    else:
        abort(404)


@app.route('/friends/requests/delete/<int:id>')
@login_required
def delete_friend_requests(id):
    session = db_session.create_session()
    # Нахождение запроса в друзья по его id
    friend_requests = session.query(FriendRequest).filter(FriendRequest.id == id)
    friend_request = friend_requests.filter((FriendRequest.sender == current_user.id) |
                                            (FriendRequest.recipient == current_user.id)).first()
    if friend_request:
        session.delete(friend_request)
        session.commit()
        session.close()
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
            comments_list_dict = [
                {
                    'id': elem.id,
                    'author': session.query(User).filter(User.id == elem.user_id).first(),
                    'comment': elem
                } for elem in news.comments[::-1]
            ]  # Все коментарии к новости
            user = news.user
            session.close()
            return render_template('view_news.html', title=f'{news.title}', news=news, form=form,
                                   comments=comments_list_dict, user=user)
        else:
            abort(404)

    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          (News.is_private == False) | (News.user == current_user)).first()
        if news:
            comment = Comment(content=form.content.data, user_id=current_user.id)
            news.comments.append(comment)
            session.commit()
            session.close()
            return redirect(f'/news/{id}')
        else:
            abort(404)


@app.route('/news/add', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        if user:
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            user.news.append(news)
            session.merge(current_user)
            session.commit()
            session.close()
            return redirect('/me')
        else:
            abort(404)
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
            session.close()
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
            session.close()
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
        session.close()
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
                   news.comments))  # Поиск коментария
        if comment:
            session.delete(comment[0])
            session.commit()
            session.close()
        else:
            abort(404)
    else:
        abort(404)
    return redirect(f'/news/{news_id}')


@app.route('/chats')
@login_required
def list_chats():
    session = db_session.create_session()
    chats = current_user.get_all_chats(session)
    chats_list_dicts = [
        {
            'id': chat.id, 'chat': chat,
            'name': str(session.query(User).filter(User.id == chat.get_opponent_id(session, current_user.id)).first())
        } for chat in chats
    ]  # Список всех чатов
    session.close()
    return render_template('chats.html', title='Чаты', chats=chats_list_dicts)


@app.route('/chats/<int:id>', methods=['GET', 'POST'])
@login_required
def view_chat(id):
    form = MessageForm()
    if request.method == "GET":
        session = db_session.create_session()
        chat = current_user.get_chat(session, id)

        if chat:
            opponent_user = session.query(User).get(chat.get_opponent_id(session, current_user.id))
            messages = chat.get_all_messages(session)
            messages_list_dicts = [
                {
                    'id': message.id, 'message': message,
                    'author': session.query(User).filter(User.id == message.user_id).first()
                } for message in messages
            ]  # Список всех сообщений
            session.close()
            return render_template('view_chat.html',
                                   title=str(opponent_user), chat=chat, form=form,
                                   messages=messages_list_dicts, User=User)
        else:
            abort(404)

    if form.validate_on_submit():
        session = db_session.create_session()
        chat = current_user.get_chat(session, id)
        if chat:
            message = Message(content=form.content.data, user_id=current_user.id, chat_id=id)
            session.add(message)
            session.commit()
            session.close()
            return redirect(f'/chats/{id}')
        else:
            abort(404)


@app.route('/chats/<int:chat_id>/delete_message/<int:message_id>')
@login_required
def delete_message(chat_id, message_id):
    session = db_session.create_session()
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        message = session.query(Message).filter(Message.id == message_id, Message.chat_id == chat_id,
                                                Message.user_id == current_user.id).first()
        if message:
            session.delete(message)
            session.commit()
            session.close()
            return redirect(f'/chats/{chat_id}')
        else:
            abort(404)
    else:
        abort(404)


@app.route('/chats/open_with_friend/<int:id>')
@login_required
def open_chat_with_user(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == id).first()
    if not user or not user.is_friend(session, current_user.id):
        # Чтобы открыть чат с пользователем, нужно чтобы он был и он был вашим другом
        abort(404)
    chat = current_user.get_chat_with_user(session, user.id)
    if not chat:
        # Если чата с пользователем не существует то он создаётся
        chat = Chat(user_a=current_user.id, user_b=id)
        session.add(chat)
        session.commit()

    # Повторный поиск необходим для предотвращения ошибки
    chat = current_user.get_chat_with_user(session, user.id)
    session.close()
    return redirect(f'/chats/{chat.id}')


@app.route('/chats/delete/<int:id>')
@login_required
def delete_chat(id):
    session = db_session.create_session()
    chat = current_user.get_chat(session, id)
    if chat:
        session.delete(chat)
        session.commit()
        session.close()
        return redirect('/chats')
    else:
        abort(404)


@app.route('/news')
@login_required
def list_news():
    session = db_session.create_session()
    friends = current_user.get_all_friends_users(session)
    news = []  # Нахождение всех новостей друзей, которые не приватны
    for friend in friends:
        news += list(filter(lambda x: not x.is_private, friend.news))

    news.sort(key=lambda x: x.created_date, reverse=True)  # Сортировка по дате создания
    news_list_dict = [
        {
            'id': elem.id,
            'user': elem.user,
            'news': elem
        } for elem in news
    ]  # Список всех новостей
    session.close()
    return render_template('all_news.html', title='Новости', news=news_list_dict)


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
        session.close()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as session:
        user = session.query(User).get(user_id)
        return user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    try:
        db_session.global_init(conn_str='postgresql://192.168.0.5:5432/social_net.sqlite')
    except sqlalchemy.exc.OperationalError:
        db_session.global_init(conn_str='sqlite:///db/db_social_network.sqlite?check_same_thread=False')

    app.run(host='0.0.0.0', port=80)


if __name__ == "__main__":
    main()
