import os
import pandas as pd
import mysql.connector
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from test_functions import *

import cv2
import face_recognition

df = pd.read_csv('db_face_reco.csv')
print(df)
print(len(df))

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_image():
    global df

    def insert_varibles_into_table(ind, user, status):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='face_reco',
                                                 user='terence',
                                                 password='1234')
            cursor = connection.cursor()
            mySql_insert_query = """INSERT INTO profiles (User_ID, Username, Status) 
                                    VALUES (%s, %s, %s) """

            record = (ind, user, status)
            cursor.execute(mySql_insert_query, record)
            connection.commit()
            print("Record inserted successfully into profiles table")

        except mysql.connector.Error as error:
            print("Failed to insert into MySQL table {}".format(error))

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

    ind = len(df)+1
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        user = request.form['nm']
        print("Username is " + user)
        if request.form.get('status1'):
            print("Status is allowed")
            df = df.append({'User_ID': ind, 'Username': user, 'Status': 'Allowed'}, ignore_index=True)
            df.to_csv('db_face_reco.csv', index=False, header=True)
            insert_varibles_into_table(ind, user, 'Allowed')
        elif request.form.get('status2'):
            print("Status is banned")
            df = df.append({'User_ID': ind, 'Username': user, 'Status': 'Banned'}, ignore_index=True)
            df.to_csv('db_face_reco.csv', index=False, header=True)
            insert_varibles_into_table(ind, user, 'Banned')
        print(df)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # print('upload_image filename: ' + filename)

        # directories
        dir_known_faces = "known_faces"
        dir_new_faces = "static/uploads"
        # dir_banned_faces = "banned_faces"

        tolerance = 0.6

        # FACE RECOGNITION

        known_faces = []
        known_names = []
        current_status = []

        load_known_faces(dir_known_faces, known_faces, current_status, known_names)

        # print(known_names)
        # print(current_status)
        print("processing unknown faces")


        image = face_recognition.load_image_file(f"{dir_new_faces}/{filename}")
        locations = face_recognition.face_locations(image, model="cnn")
        encodings = face_recognition.face_encodings(image, locations)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        for face_encoding, face_location in zip(encodings, locations):
            results = face_recognition.compare_faces(known_faces, face_encoding, tolerance)
            # print(results)
            # match = None
            # status_match = None
            top_left = (face_location[3], face_location[0])
            bottom_right = (face_location[1], face_location[2] + 5)
            # print(top_left)
            # print(bottom_right)
            # To fill text color
            # top_left_text = (face_location[3], face_location[2] + 5)
            # bottom_right_text = (face_location[1], face_location[2] + 22)

            color_known = [0, 255, 0]
            color_banned = [0, 0, 255]
            color_new = [0, 128, 255]

            if True in results:
                status_match = current_status[results.index(True)]
                match = known_names[results.index(True)]
                if status_match == "allowed":
                    print(f"Match found: {match}")
                    cv2.rectangle(image, top_left, bottom_right, color_known, 2)
                    # cv2.rectangle(image, top_left_text, bottom_right_text, color_known, cv2.FILLED)
                    cv2.putText(image, match, (face_location[3], face_location[2] + 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (200, 200, 200))
                elif status_match == "banned":
                    print(f"Match found: {match}")
                    cv2.rectangle(image, top_left, bottom_right, color_banned, 2)
                    # cv2.rectangle(image, top_left_text, bottom_right_text, color_banned, cv2.FILLED)
                    cv2.putText(image, match, (face_location[3], face_location[2] + 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (200, 200, 200))
            elif False in results:
                print("Match not found")
                cv2.rectangle(image, top_left, bottom_right, color_new, 2)
                # cv2.rectangle(image, top_left_text, bottom_right_text, color_new, cv2.FILLED)
                cv2.putText(image, "unknown", (face_location[3], face_location[2] + 20), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (200, 200, 200))


            cv2.imwrite(f"static/new_faces/{filename}", image)

            # END OF FACE RECO

        flash('Image successfully uploaded and displayed below')
        return render_template('upload.html', filename=filename)
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/display/<filename>')
def display_image(filename):
    print(filename)
    # print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='new_faces/' + filename), code=301)


if __name__ == "__main__":
    app.run()