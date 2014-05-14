import os
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request, session, g, redirect, url_for, render_template, flash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

'''Configuration - Debug can be removed for production use'''
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI ='sqlite:///' + os.path.join(basedir, 'data.sqlite'),
    SECRET_KEY='not a password',
    DEBUG=True,
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True,
    USERNAME='admin',
    PASSWORD='default'
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

db = SQLAlchemy(app)

'''Data model - one (Post) to many (Comment)'''
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post %r>' % self.title 

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    reply = db.Column(db.Text, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def __repr__(self):
        return '<Comment %r>' % self.reply

'''index page showing all posts'''
@app.route('/')
def show_entries():
    entries = Post.query.order_by(Post.id.desc()).all()
    return render_template('show_entries.html', entries=entries)

'''url for each post and its guest comments'''
@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    comments = post.comments.all()
    if request.method == 'POST':
        addcomments = Comment(reply=request.form['reply'], post=post)
        db.session.add(addcomments)
        return redirect(url_for('show_entries'))
    return render_template('post.html', post=post, comments=comments)

'''add a post if the admin is logged in'''
@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        post=Post(title=request.form['title'], text=request.form['text'])
        db.session.add(post)
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))
    return render_template('add.html')

'''delete a post if admin is logged in'''
@app.route('/delete/<int:id>')
def delete_entry(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        post = Post.query.get_or_404(id)
        db.session.delete(post)
        flash('The post has been deleted')
        return redirect(url_for('show_entries'))

'''login page with error message'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

'''log admin out; return None if key 'logged_in' doesn't exsit'''
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()