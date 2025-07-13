from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import uuid
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ARTICLES_FILE = 'articles.json'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Utility functions
def load_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_articles(articles):
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(articles, f, indent=4)

# Routes
@app.route('/')
@app.route('/articles')
def list_articles():
    articles = load_articles()
    return render_template('article_list.html', articles=articles)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        body = request.form['body']
        image = request.files.get('image')

        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = url_for('static', filename=f'uploads/{filename}')

        articles = load_articles()
        article_id = str(uuid.uuid4())
        articles[article_id] = {
            'id': article_id,
            'title': title,
            'author': author,
            'body': body,
            'image_url': image_url
        }
        save_articles(articles)
        return redirect(url_for('view_article', article_id=article_id))
    return render_template('edit_post.html')

@app.route('/edit/<article_id>', methods=['GET', 'POST'])
def edit_post(article_id):
    articles = load_articles()
    article = articles.get(article_id)
    if not article:
        return "Article not found", 404

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        body = request.form['body']
        image = request.files.get('image')

        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            article['image_url'] = url_for('static', filename=f'uploads/{filename}')

        article.update({
            'title': title,
            'author': author,
            'body': body
        })

        articles[article_id] = article
        save_articles(articles)
        return redirect(url_for('view_article', article_id=article_id))

    return render_template('edit_post.html', article=article)

@app.route('/article/<article_id>')
def view_article(article_id):
    articles = load_articles()
    article = articles.get(article_id)
    if not article:
        return "Article not found", 404
    return render_template('article_view.html', article=article)


@app.route('/delete/<article_id>', methods=['POST'])
def delete_article(article_id):
    articles = load_articles()
    article = articles.get(article_id)
    if not article:
        return "Article not found", 404

    # Optional: Delete associated image file
    if article.get('image_url'):
        image_path = article['image_url'].replace('/static/', 'static/')
        if os.path.exists(image_path):
            os.remove(image_path)

    del articles[article_id]
    save_articles(articles)
    return redirect(url_for('list_articles'))


if __name__ == '__main__':
    app.run(debug=True)
