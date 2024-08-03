import os
from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime
import logging

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = app.logger

# Use environment variable for data file path, with a default
DATA_FILE = os.environ.get('DATA_FILE', 'posts.json')

def load_posts():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        return []
    except Exception as e:
        logger.error(f"Error loading posts: {str(e)}", exc_info=True)
        return []

def save_posts(posts):
    try:
        with open(DATA_FILE, 'w') as file:
            json.dump(posts, file, indent=4)
    except Exception as e:
        logger.error(f"Error saving posts: {str(e)}", exc_info=True)
        raise

def calculate_streak(posts):
    if not posts:
        return 0

    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    streak = 1
    last_date = datetime.fromisoformat(posts[0]['timestamp']).date()

    for post in posts[1:]:
        post_date = datetime.fromisoformat(post['timestamp']).date()
        if (last_date - post_date).days == 1:
            streak += 1
            last_date = post_date
        else:
            break

    if (datetime.now().date() - last_date).days > 1:
        streak = 0

    return streak

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def get_posts():
    try:
        posts = load_posts()
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(posts)
    except Exception as e:
        logger.error(f"Error in get_posts: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/add', methods=['POST'])
def add_post():
    try:
        logger.info("Received add post request")
        posts = load_posts()
        new_post = request.json
        logger.info(f"Received post data: {new_post}")
        
        if not new_post or 'content' not in new_post:
            logger.warning("Invalid post data received")
            return jsonify({"error": "Invalid post data"}), 400
        
        new_post['id'] = max([post['id'] for post in posts], default=0) + 1
        new_post['timestamp'] = datetime.now().isoformat()
        posts.append(new_post)
        save_posts(posts)
        
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        logger.info("Post added successfully")
        return jsonify(posts)
    except Exception as e:
        logger.error(f"Error in add_post: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/edit/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    try:
        logger.info(f"Received edit post request for post_id: {post_id}")
        posts = load_posts()
        edited_post = request.json
        logger.info(f"Received edited post data: {edited_post}")
        
        if not edited_post or 'content' not in edited_post:
            logger.warning("Invalid post data received")
            return jsonify({"error": "Invalid post data"}), 400
        
        for post in posts:
            if post['id'] == post_id:
                post['content'] = edited_post['content']
                post['timestamp'] = datetime.now().isoformat()
                break
        else:
            logger.warning(f"Post with id {post_id} not found")
            return jsonify({"error": "Post not found"}), 404
        
        save_posts(posts)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        logger.info("Post edited successfully")
        return jsonify(posts)
    except Exception as e:
        logger.error(f"Error in edit_post: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        logger.info(f"Received delete post request for post_id: {post_id}")
        posts = load_posts()
        original_length = len(posts)
        posts = [post for post in posts if post['id'] != post_id]
        
        if len(posts) == original_length:
            logger.warning(f"Post with id {post_id} not found")
            return jsonify({"error": "Post not found"}), 404
        
        save_posts(posts)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        logger.info("Post deleted successfully")
        return jsonify(posts)
    except Exception as e:
        logger.error(f"Error in delete_post: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/test', methods=['GET'])
def test():
    try:
        logger.info("Test route accessed")
        return jsonify({"message": "Test successful", "data_file": DATA_FILE}), 200
    except Exception as e:
        logger.error(f"Error in test route: {str(e)}", exc_info=True)
        return jsonify({"error": "Test failed", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
