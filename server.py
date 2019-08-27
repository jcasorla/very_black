from flask import Flask, render_template, request, redirect,session, flash
from mysqlconnection import connectToMySQL
import re	# the regex module
from flask_bcrypt import Bcrypt        



#secret key required for session
app = Flask(__name__)
app.secret_key = 'keep it secret, keep it safe' # set a secret key for security purposes
bcrypt = Bcrypt(app)     # we are creating an object called bcrypt, 
                         # which is made by invoking the function Bcrypt with our app as an argument

myDB='test'

# create a regular expression object that we'll use later   
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

@app.route('/')
def index():
    return render_template("index.html")


#**********************Register*************************
@app.route('/users', methods=['POST'])
def create_user():
    print("Got Post Info")
    print(request.form)
    
    failed=False
    
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==True):            
            flash("Please chose another email")
            failed=True

    if len(request.form['first_name']) < 1:
        flash("first name cannot be blank!")
        failed=True
    if len(request.form['last_name']) < 1:
        flash("last name cannot be blank!")
        failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True
    if len(request.form['cpwd']) < 1:
        flash("confirm password cannot be blank!")
        failed=True
    if request.form['pwd'] != request.form['cpwd']:
        flash("Passwords do not match")
        failed=True
        

    if(failed==True):
        return redirect("/")

    
    elif not '_flashes' in session.keys():	# no flash messages means all validations passed
        pw_hash = bcrypt.generate_password_hash(request.form['pwd'])
                
        query="insert into users (first_name,last_name,email,password,created_at,updated_at)  values (%(fn)s,%(ln)s,%(em)s,%(pw)s, NOW(),NOW());"

        data = {
            "fn": request.form['first_name'],
            "ln": request.form['last_name'],
            "em": request.form['email'],
            "pw": pw_hash
        }
        mysql = connectToMySQL(myDB)
        id=mysql.query_db(query,data)
        print(id)

        query2="select * from users where id=%(id)s"
        data2 = {
            "id": id            
        }

        mysql = connectToMySQL(myDB)
        user=mysql.query_db(query2,data2)[0]

        session['id']=id
        session['name']=user['first_name']
        return redirect('/show_jobs')



#**********************login*************************
@app.route('/login', methods=['POST'])
def login():
    failed=False
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==False):            
            flash("Unable to Login")
            failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True

    elif not '_flashes' in session.keys():
        print(request.form["email"])
        mysql = connectToMySQL(myDB)
        query = "SELECT * FROM users WHERE email like %(em)s;"
        data = { "em" : request.form["email"] }
        result = mysql.query_db(query, data)
        if len(result) > 0:
            if bcrypt.check_password_hash(result[0]['password'], request.form['pwd']):
                # if we get True after checking the password, we may put the user id in session
                #change it to session['id']
                session['id'] = result[0]['id']
                session['name'] = result[0]['first_name']
                # never render on a post, always redirect!
                # return redirect('/success')
            else:
                flash("Unable to Login")
                print("Unable to login")
                failed=True

    if(failed==True):
        return redirect("/")
    else:
        return redirect("/show_jobs")#change

#**********************jobs dashboard*************************
@app.route('/show_jobs')
def showjobs():

    print(session['id'])

    if(bool(session)):
        #select * from jobs;
        query="select j.id,j.title,j.location, j.user_id, j.description,j.category from jobs j where j.id not in (select job_id from assignment)"

        data = {
            "id": session['id']
        }
        mysql = connectToMySQL(myDB)
        jobs=mysql.query_db(query,data)

   
        #select j.title,j.user_id from jobs j join assignment a on a.job_id=j.id where a.user_id=%(id)s

        query2="select j.title,a.user_id,a.job_id from jobs j join assignment a on a.job_id=j.id where a.user_id=%(id)s;"

        data2 = {
            "id": session['id']
        }
        mysql = connectToMySQL(myDB)
        my_jobs=mysql.query_db(query2,data2)
               

        return render_template("show_jobs.html", all_jobs=jobs, my_jobs=my_jobs)
    else:
        return redirect("/")

#**********************show add job page*************************
@app.route("/jobs/new")
def add_job_page():

    return render_template("add_job.html")

#**********************insert job*************************
@app.route("/jobs/insert", methods=['POST'])
def insert_job():

    #validations for adding jobs 
    failed_form = False
    if len(request.form['title']) < 3:
        flash("Title field is required and must be atleast 3 characters long")
        failed_form=True

    else:
        query="select * from jobs where title=%(title)s"

        data = {
            "title": request.form['title']
        }
        mysql = connectToMySQL(myDB)
        result=mysql.query_db(query,data)

        print(type(result))

    
        if(not result):
            pass
        else:
            flash("Title exists please chose another")
            failed_form=True

    if len(request.form['description']) < 3:
        flash("Description is required and cannot be less than 3 characters")
        failed_form=True
    
    if len(request.form['location']) < 3:
        flash("location is required and cannot be less than 3 characters")
        failed_form=True
    
    if failed_form == True:
        return redirect("/jobs/new")
    

    elif not '_flashes' in session.keys():
        query="insert into jobs (title,location,description,user_id,created_at,updated_at)  values (%(title)s,%(locat)s,%(desc)s,%(id)s, NOW(),NOW());"

        data = {
            "title": request.form['title'],
            "desc": request.form['description'],
            "locat": request.form['location'],
            "id": session['id']
        }
        mysql = connectToMySQL(myDB)
        mysql.query_db(query,data)

    return redirect("/show_jobs")

#**********************view job page*************************
@app.route('/jobs/<int:id>')
def view_job(id):

    query="select * from jobs where id=%(id)s"

    data = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    job=mysql.query_db(query,data)[0]

    query2="select j.id,j.title,a.user_id,a.job_id from jobs j join assignment a on a.job_id=j.id where a.user_id=%(id)s;"

    data2 = {
        "id": session['id']
    }
    mysql = connectToMySQL(myDB)
    liked=mysql.query_db(query2,data2)

    if len(liked) > 0:
        liked = True
    else:
        liked = False
    
    
    return render_template("view_job.html",job=job,liked=liked)

#**********************edit job page*************************
@app.route('/jobs/<int:id>/edit')
def edit_job(id):

    query="select * from jobs where id=%(id)s"

    data = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    job=mysql.query_db(query,data)[0]

    mysql = connectToMySQL(myDB)
    
    return render_template("edit_job.html",job=job)

#**********************update job*************************
@app.route('/jobs/<int:id>/update', methods=['POST'])
def update_job(id):
    #validations for updating jobs 
    failed_form = False
    if len(request.form['title']) < 3:
        flash("Title field is required and must be atleast 3 characters long")
        failed_form=True

    else:
        query="select * from jobs where title=%(title)s"

        data = {
            "title": request.form['title']
        }
        mysql = connectToMySQL(myDB)
        result=mysql.query_db(query,data)

        print(type(result))

    
        if(not result):
            pass
        else:
            flash("Title exists please chose another")
            failed_form=True

    if len(request.form['description']) < 3:
        flash("Description is required and cannot be less than 3 characters")
        failed_form=True
    
    if len(request.form['location']) < 3:
        flash("location is required and cannot be less than 3 characters")
        failed_form=True
    
    if failed_form == True:
        return redirect(f"/jobs/{id}/edit")
    

    elif not '_flashes' in session.keys():
        query="update jobs set title=%(title)s,description=%(desc)s,location=%(locat)s where id=%(id)s"

        data = {
            "id": id,
            "title": request.form['title'],
            "desc": request.form['description'],
            "locat": request.form['location']
        }
        mysql = connectToMySQL(myDB)
        mysql.query_db(query,data)
    
    return redirect("/show_jobs")

#**********************delete job*************************
@app.route('/jobs/<int:id>/delete')
def delete_job(id):
    del_assign(id)
    
    query="delete from jobs where id=%(id)s"

    data = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)

    return redirect("/show_jobs")

#**********************add assignment to job *************************
@app.route('/jobs/<int:id>/assign')
def assign_job(id):
    print("im here")
    query="insert into assignment (user_id,job_id) values(%(id)s,%(j_id)s);"

    data = {
        "j_id": id,        
        "id": session['id']
    }
    mysql = connectToMySQL(myDB)
    id=mysql.query_db(query,data)
    return redirect("/show_jobs")

#**********************remove assignment from job *************************
@app.route('/jobs/<int:id>/assign/del')
def del_assign(id):
    query="delete from assignment where job_id=%(j_id)s and user_id=%(id)s"

    data = {
       "j_id": id,        
        "id": session['id']
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)

    return redirect("/show_jobs")




@app.route('/logout')
def logout():

    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)  