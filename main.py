from flask import Flask, request, jsonify
import jwt
from functools import wraps
from bson import ObjectId, json_util
from mongo_db import db
from waitress import serve

app = Flask(__name__)
# SECRET_KEY for authentication
app.config['SECRET_KEY'] = 'e0945f09d29c8b563347fdfe355329c0db379ff3f4adcc26b2f3d525d95b2ba8'
# algorithm for token_encoding and decode
ALGORITHM = "HS256"


# token validation
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['token'].split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=ALGORITHM)
            _id = ObjectId(data['user_id'])
            current_user = db['user_details'].find_one({'_id': _id})
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    password = data['password']

    user = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password
    }
    try:
        email_list: list = []
        for i in db['user_details'].find():
            email_list.append(i['email'])
        if not user['email'] in email_list:
            db['user_details'].insert_one(user)
            result = {'message': 'User registered successfully!'}
            return result, 200
    except Exception as e:
        print('error', e)
    error_message = {'error': 'Email already Exists'}
    return error_message, 500


# login
@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic'}), 401

    user = db['user_details'].find_one({'email': auth.username})

    if not user:
        return jsonify({'message': 'User not found'}), 401

    if user['password'] == auth.password:
        token = jwt.encode({'user_id': str(user['_id'])}, app.config['SECRET_KEY'], algorithm=ALGORITHM)
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials'}), 401


# add new templates
@app.route('/template', methods=['POST'])
@token_required  # token verification annotation
def create_template(current_user):
    data = request.get_json()
    template_name = data['template_name']
    subject = data['subject']
    body = data['body']

    template = {
        'template_name': template_name,
        'subject': subject,
        'body': body,
        'user_id': current_user['_id']
    }
    db['templates'].insert_one(template)
    return jsonify({'message': 'Template created successfully!'})


# get_all template method
@app.route('/template', methods=['GET'])
@token_required
def get_all_templates(current_user):
    templates = list(i for i in db['templates'].find({}))

    for template in templates:
        oid = ObjectId(template['_id'])
        oid_str = str(oid)
        template['_id'] = oid_str
    # serialization
    return json_util.dumps({'templates': templates})


# get_single template method
@app.route('/template/<template_id>', methods=['GET'])
@token_required
def get_template(current_user, template_id):
    _id = ObjectId(template_id)
    template = db['templates'].find_one({'_id': _id})
    if template:
        return json_util.dumps({'template': template})
    return jsonify({'message': 'Template not found'}), 404


# update_single template method
@app.route('/template/<template_id>', methods=['PUT'])
@token_required
def update_template(current_user, template_id):
    data = request.get_json()
    template_name = data['template_name']
    subject = data['subject']
    body = data['body']

    _id = ObjectId(template_id)

    template = db["templates"].find_one({'_id': _id, 'user_id': current_user['_id']})

    if template:
        db['templates'].update_one(
            {'_id': _id, 'user_id': current_user['_id']},
            {'$set': {'template_name': template_name, 'subject': subject, 'body': body}}
        )
        return jsonify({'message': 'Template updated successfully!'})

    return jsonify({'message': 'Template not found'}), 404


# delete template
@app.route('/template/<template_id>', methods=['DELETE'])
@token_required
def delete_template(current_user, template_id):
    _id = ObjectId(template_id)
    template = db['templates'].find_one({'_id': _id, 'user_id': current_user['_id']})

    if template:
        db['templates'].delete_one({'_id': _id, 'user_id': current_user['_id']})
        return jsonify({'message': 'Template deleted successfully!'})

    return jsonify({'message': 'Template not found'}), 404


if __name__ == '__main__':
    # host_connection
    serve(app, host='0.0.0.0', port=5000)
