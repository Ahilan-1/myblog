from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'posts.json'

def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_posts(posts):
    with open(DATA_FILE, 'w') as file:
        json.dump(posts, file, indent=4)

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
    posts = load_posts()
    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(posts)

@app.route('/add', methods=['POST'])
def add_post():
    try:
        posts = load_posts()
        new_post = request.json
        if not new_post or 'content' not in new_post:
            return jsonify({"error": "Invalid post data"}), 400
        
        new_post['id'] = max([post['id'] for post in posts], default=0) + 1
        new_post['timestamp'] = datetime.now().isoformat()
        posts.append(new_post)
        save_posts(posts)
        
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(posts)
    except Exception as e:
        app.logger.error(f"Error in add_post: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/edit/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    try:
        posts = load_posts()
        edited_post = request.json
        if not edited_post or 'content' not in edited_post:
            return jsonify({"error": "Invalid post data"}), 400
        
        for post in posts:
            if post['id'] == post_id:
                post['content'] = edited_post['content']
                post['timestamp'] = datetime.now().isoformat()
                break
        else:
            return jsonify({"error": "Post not found"}), 404
        
        save_posts(posts)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(posts)
    except Exception as e:
        app.logger.error(f"Error in edit_post: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        posts = load_posts()
        posts = [post for post in posts if post['id'] != post_id]
        save_posts(posts)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(posts)
    except Exception as e:
        app.logger.error(f"Error in delete_post: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
