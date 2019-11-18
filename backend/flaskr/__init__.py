import os
from flask_cors import CORS
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r"*": {"origins": '*'}})

  @app.after_request
  def after_request(response):
    response.headers.add(
      'Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add(
      'Access-Control-Allow-Methods', 'POST, PATCH, PUT, GET, OPTIONS, DELETE'
    )
    return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  
  @app.route('/categories')
  def get_categories():
    try:
      categories = Category.query.order_by(Category.id).all()
      for i in categories:
        result = []
        result.append(i.type)
        if categories == []:
          abort(404)
        return jsonify({
          'success': True,
          'categories': result
        })
    except Exception as error:
      return error


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''

  def paginate(selection, model):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    selections = model.query.order_by(model.id).all()
    formated_content = [content.format() for content in selections]
    current_selection = formated_content[start:end]
    return current_selection


  @app.route('/questions')
  def get_requests():
    try:
      questions = Question.query.order_by(Question.id).all()
      categories = Category.query.order_by(Category.id).all()
      result = []
      for i in categories:
        result.append(i.type)

        if questions == []:
          abort(404)
        return jsonify({
          "questions": paginate(questions, Question),
          "total_questions": len(questions),
          "current_category": len(paginate(questions, Question)),
          "categories": result,
          "success": True
        }), 200
    except Exception as error:
      abort(442)

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    try:
      if not question:
        abort(404, 'not found')
      
      else:
        question.delete()
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.order_by(Category.id).all()
        result = []
        for i in categories:
          result.append(i.type)
  
        return jsonify({
            "questions": paginate(questions, Question),
            "total_questions": len(questions),
            "current_category": len(paginate(questions, Question)),
            "categories": result,
            "success": True

          }), 200
    except Exception as error:
      abort(422)


  @app.route('/questions', methods=['POST'])
  def add_question():
    Request = request.get_json()
    question = Request.get('question', None)
    answer = Request.get('answer', None)
    category = Request.get('category', None)
    difficulty = Request.get('difficulty', None)
    try:
      body = Question(
        question=question, answer=answer,
        category=category, difficulty=difficulty
        )
      if not question or not answer or not category or not difficulty:
        return jsonify({
          'message': 'please fill out the missing fields'
          }), 400
      else:
        body.insert()
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.order_by(Category.id).all()
        formated_questions = [question.format() for question in questions]
        result = []
        for i in categories:
          result.append(i.type)
          return jsonify({
              "questions": paginate(formated_questions, Question),
              "total_questions": len(questions),
              "current_category": len(paginate(questions, Question)),
              "categories": result,
              "success": True
            }), 200
    except Exception as error:
      abort(422)

  @app.route('/questions/search', methods=["POST"])
  def search_question():
    search_term = request.get_json().get('searchTerm', None)
    try:
      if search_term == '':
        abort(400, 'search field is blank')
      else:
        search_results = db.session.query(Question).with_entities(
          Question.question, Question.category,
          Question.category, Question.difficulty
        ).filter(Question.question.ilike(
          '%'+ search_term +'%'
        )).all()

        if search_results:
          return jsonify({
                  'success': True,
                  'questions': paginate(search_results, Question),
                  'total_questions': len(search_results),
                  'current_category': len(paginate(search_results, Question))
              }), 200
        else:
          abort(404, 'no questions found')
    except Exception as error:
      abort(422)


  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions(category_id):
    try:
      questions = Question.query.order_by(Question.id).filter_by(
        category=str(category_id)
      ).first()
      print(questions)
      if questions is None:
        abort(404)
      else:
        categories = Category.query.order_by(Category.id).all()
        result = []
        for i in categories:
          result.append(i.type)
          return jsonify({
                "questions": paginate(questions, Question),
                # "total_questions": len(questions),
                "current_category": len(paginate(questions, Question)),
                "categories": result,
                "success": True
              }), 200
    except:
      abort(422)


  @app.route('/quizzes', methods=['POST'])
  def get_quizzes():
   
    try:
      data = request.get_json()
      previous_questions = data.get("previous_questions", None)
      quiz_category = data.get("quiz_category", None)
      quiz_category_id = int(quiz_category["id"])

      question = Question.query.filter(
          Question.id.notin_(previous_questions)
      )

      if quiz_category_id:
          question = question.filter_by(category=quiz_category_id)

      question = question.first().format()

      return jsonify({"success": True, "question": question,}), 200
    except Exception as error:
        raise error      
    finally:
      db.session.close()  

  @app.errorhandler(400)
  def custom404(error):
      response = jsonify({
          'success': False,
          'message': 'Bad Request'
      })
      return response, 400


  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      "error": 422,
      'message': "unprocessable"
    })

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      "error": 400,
      'message': "Bad request"
    })

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      "error": 404,
      'message': "Not Found"
    }),404
  return app
  