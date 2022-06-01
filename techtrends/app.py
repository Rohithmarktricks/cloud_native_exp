import sqlite3
import logging
from time import asctime
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


def log_info_level(message):
    """
    Add info level log to the app's logger
    ======================================

    Parameters
    ----------
    message : str
        Message to log.
    """

    app.logger.info('{}:{}'.format(asctime(), message))



def log_error_level(message):
    """
    Add error level log to the app's logger
    =======================================

    Input Params:
    ------------
    message: str
        Message to log
    """

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    log_info_level('2020 CNCF Annual Report is retrieved.')
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        log_info_level('Post: Failed to get #{}.'.format(post_id))
        return render_template('404.html'), 404
    else:
        log_info_level('Post: Article "{}" is retrieved'.format(post['title']))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log_info_level('About Us page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            log_info_level('Create: new article created "{}".'.format(title))
            return redirect(url_for('index'))

    log_error_level('Create: Failed to create article because of missing title.')
    return render_template('create.html')

# Define the Healthcheck endpoint
@app.route('/healthz')
def healthz():
    """
    Added function that peforms health check
    ========================================
    """

    response = app.response_class(response=json.dumps({'result' : 'OK - healthy'}),
                                  status=200, mimetype='application/json')
    try:
        connection = get_db_connection()
        connection.execute('SELECT 1 FROM posts').fetchone()
        connection.close()
        log_info_level('Healthcheck: ok')
    except Exception:
        response = app.response_class(
                        response=json.dumps({'result' : 'Error - not healthy'}),
                                      status=200, mimetype='application/json')
        log_error_level('Healthcheck: failed')
    return response

# Define the Metrics endpoint
@app.route('/metrics')
def metrics():
    """
    Added function that peforms metrics check
    =========================================
    """

    metrics_obj = {
    'db_connection_count': 0,
    'post_count': None
    }

    try:

        connection = get_db_connection()
        article_count = connection.execute('SELECT 1 FROM posts').fetchone()
        connection.close()

        metrics_obj['db_connection_count'] += 1
        metrics_obj['post_count'] = article_count[0]

        log_info_level('Metrics: @ {} posts, {} connections'.format(metrics_obj['post_count'], 
                                            metrics_obj['db_connection_count']))
        
        response = app.response_class(
                response=json.dumps(metrics_obj),
                status=200,
                mimetype='application/json')

    except  Exception as e:
        log_error_level("Metrics: Failed to accumulate, check db connection")
        response  = app.response_class(
            response  = json.dumps({'result': "Error - couldn't get metrics as db connection is broken"}),
            status=200, mimetype='application/json')


    return response
        


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
