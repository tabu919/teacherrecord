from flask import Flask, jsonify, request, make_response
from http import HTTPStatus
from flask_sqlalchemy import SQLAlchemy  
from marshmallow import fields,ValidationError #handle ValidationError
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.types import TypeDecorator
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


### ERRORS HANDLING ##
def page_not_found(e):  # error:URL Not Found
    return jsonify({'message': 'URL not found !!'}), HTTPStatus.NOT_FOUND
def BAD_REQUEST(e): #errpr: check syntax error, Invalid Request message
    return jsonify({'message': 'BAD REQUEST !! Syntax, Invalid Request Message Framing, Or Deceptive Request Routing'}), HTTPStatus.BAD_REQUEST
def method_not_allowed(e): # error:when you pass wrong url
    return jsonify({'message': 'Method Not Allowed !!'}), HTTPStatus.METHOD_NOT_ALLOWED

### DATABASE DEFINITION ###
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///teacher.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False


def init_db():
    Base.metadata.create_all(bind=engine)

app.register_error_handler(404,page_not_found)
app.register_error_handler(400,BAD_REQUEST)
app.register_error_handler(405,method_not_allowed)
db=SQLAlchemy(app)


##### MODELS #####

class teacher(db.Model):
    teacher_id=db.Column(db.Integer, primary_key=True)
    teacher_name=db.Column(db.String(20), nullable=False)
    subject_id=db.Column(db.Integer, nullable=False)
    subject_name=db.Column(db.String(20), nullable=False)
    

    def create(self):
       db.session.add(self)
       db.session.commit()
       return self

    def __init__(self, teacher_name, subject_id, subject_name):
            self.teacher_name = teacher_name
            self.subject_id = subject_id
            self.subject_name = subject_name

    def __repr__(self):
                return f"{self.teacher_id}"



### Custom validator ###
def must_not_be_blank(data):
    if not data:
        raise ValidationError("Can't be Empty!") #raise Validation error on empty input data

def null_and_type_check(data, teacherObject): #check for not empty-string data input
   messageString = []
   emptyVariables = []   
   if data.get('teacher_name'):
      teacherObject.teacher_name = data['teacher_name']
      if type(teacherObject.teacher_name)!=str:
         messageString.append("Incorrect data type: Teacher name needs to be String")
      if type(teacherObject.teacher_name)==str and data.get('teacher_name').strip() == '':
         emptyVariables.append("Empty Field Error: Teacher Name cannot be empty")
   else:
      emptyVariables.append("Empty Field Error: Teacher Name cannot be empty")
   if data.get('subject_id'):
      teacherObject.subject_id = data['subject_id']
      if type(teacherObject.subject_id)!=int:
         messageString.append("Incorrect data type: Subject Id needs to be Integer")
      if type(teacherObject.subject_id)==int and data.get('subject_id') == '':
         emptyVariables.append("Empty Field Error: Subject Id cannot be empty")
   else:
      emptyVariables.append("Empty Field Error: Subject Id cannot be empty")
   if data.get('subject_name'):
      teacherObject.subject_name = data['subject_name']
      if type(teacherObject.subject_name)!=str:
         messageString.append("Incorrect data type: Subject Name needs to be String")
      if type(teacherObject.subject_name)==str and data.get('subject_name').strip() == '':
         emptyVariables.append("Empty Field Error: Subject Name cannot be empty")
   else:
      emptyVariables.append("Empty Field Error: Subject Name cannot be empty")
   output = emptyVariables + messageString
   if output:
      return ', '.join(output)
   else:
      return '' 
        
### SCHEMAS ###
class teacherSchema(ModelSchema):
      class Meta(ModelSchema.Meta):
           model = teacher
           sqla_session = db.session
      teacher_id = fields.Integer(dump_only=True)
      teacher_name = fields.String(required=True,validate=must_not_be_blank)  #custom error 
      subject_id = fields.Integer(required=True,validate=must_not_be_blank)  #custom error
      subject_name = fields.String(required=True,validate=must_not_be_blank)

##### API #####

# Get All teachers    
@app.route('/teachers', methods=['GET'])
def get_all_teachers():
   
   get_all = teacher.query.all()
   teacher_schema = teacherSchema(many=True)
   teachers = teacher_schema.dump(get_all)
   if teachers:
      return make_response(jsonify({"Teachers": teachers}),HTTPStatus.OK)
   return jsonify({'message': 'No teachers found !'}), HTTPStatus.NOT_FOUND

# Get teacher By id's
@app.route('/teachers/<int:teacher_id>', methods=['GET'])
def get_teacher_by_id(teacher_id):
   get_tea = teacher.query.get(teacher_id)
   teacher_schema = teacherSchema()
   teachers = teacher_schema.dump(get_tea)
   if teachers:
          return make_response(jsonify({"Teachers": teachers}),HTTPStatus.OK)
   return jsonify({'message': 'No teachers found'}), HTTPStatus.NOT_FOUND

#Add teacher
@app.route('/teachers', methods=['POST'])
def add_teacher():
   data = request.get_json()
   if not data:
        return {"message": "No input data provided"},400 #error:data is not in json format
   teacher_schema = teacherSchema()
   try:
      teachers = teacher_schema.load(data)
   except ValidationError as err:
        return err.messages, 422    #error: invalid datatype of input data
   improper_data = null_and_type_check(data, teachers)
   if improper_data:
      return {"message": improper_data}, 422
   results = teacher_schema.dump(teachers.create())
   return make_response(jsonify({"Teacher": results})),HTTPStatus.CREATED
   
#Update teacher
@app.route('/teachers/<int:teacher_id>', methods=['PUT'])
def update_teachers(teacher_id):
      data=request.get_json()
      if not data:
        return {"message": "No input data provided"} ,400 #error:data is not in json format
      get_teacher=teacher.query.get(teacher_id)
      if(get_teacher == None):
         return {"message": "Teacher Id doesn't exist, can't update!"}, 404
      improperData = null_and_type_check(data, get_teacher) #error: check for not empty-string data input
      if improperData:
            return {"message": improperData}, 422
      db.session.add(get_teacher)
      db.session.commit()
      teacher_schema = teacherSchema(only=['teacher_id', 'teacher_name', 'subject_id', 'subject_name'])
      teachers = teacher_schema.dump(get_teacher)
      if teachers:
          return make_response(jsonify({"Teachers": teachers})),HTTPStatus.OK
      return jsonify({'message': 'teacher with teacher Id not found'}),HTTPStatus.NOT_FOUND 
     
#Delete teacher By ID
@app.route('/teachers/<int:teacher_id>', methods=['DELETE'])
def delete_teacher_by_id(teacher_id):
   get_teacher = teacher.query.get(teacher_id)
   if get_teacher:
      db.session.delete(get_teacher)
      db.session.commit()
      return make_response(jsonify({'message':'Teacher Deleted!'})),HTTPStatus.OK # teacher with teacherid deleted sucessfully
   return jsonify({'message': 'teacher not found'}), HTTPStatus.NOT_FOUND  #error:if teacher not found in database



  

if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0',port='5000')
