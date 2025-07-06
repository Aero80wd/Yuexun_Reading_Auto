from flask import Blueprint,render_template,request,redirect,url_for,flash,abort,jsonify
from forms import *
import base64
from sm4 import SM4Key
import requests
import threading
from ai_ans import *
from queue import Queue
log_session = {}

SM_KEY = bytes.fromhex("918ba21cd1253de294b35394c58ad576")
main = Blueprint('main',__name__)
@main.route('/',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        key = SM4Key(SM_KEY)
        sm4_pwd = base64.b64encode(key.encrypt(bytes(form.password.data, encoding="utf-8"), padding=True)).decode("utf-8")
        print(sm4_pwd)

        login_req = requests.post("https://www.yuexunedu.com/store/api/v1.0/safetyLogin.json", data={
            "website": "https://www.yuexunedu.com/home/2.0/login/#/login",
            "username": form.username.data,
            "password": sm4_pwd,
            "captchaUuid": "",
            "accountIdentityEnum": "2",
            "sessionUuid": ""
        })
        print(login_req.json())
        if login_req.json()["status"] != "200":
            flash(login_req.json()["message"])
            return redirect(url_for('main.login'))
        family_inf = requests.post("https://www.yuexunedu.com/store/api/v1.0/inquireFamilyStudentListAccount.json",
                                   data={"sessionUuid": login_req.json()["datas"][0]["sessionUuid"]}).json()
        requests.post("https://www.yuexunedu.com/store/api/v1.0/selectFamilyStudent.json",
                      data={"sessionUuid": login_req.json()["datas"][0]["sessionUuid"],
                            "familyStudentId": family_inf["datas"][0]["familyStudentId"]})
        log_session[login_req.json()["datas"][0]["sessionUuid"]] = Queue()
        return redirect(url_for('main.books',sessionUuid=login_req.json()["datas"][0]["sessionUuid"]))
    return render_template('login.html',form=form)
def startBookProcess(sessionUuid):
    logs = log_session[sessionUuid]
    tasks = requests.post("https://www.yuexunedu.com/store/api/v1.0/inquireReadingStudentTaskListAccount.json",
                          data={"sessionUuid": sessionUuid}).json()
    print({"sessionUuid": sessionUuid})
    if tasks["status"] != "200":
        raise Exception("Request Failed!" + str(tasks))
    tasks = tasks["datas"]
    logs.put("成功获取所有书籍信息！开始自动答题！")
    for task in tasks:
        if task["acceptTask"]:
            for book in task["bookList"]:
                book_book = Book(book["bookId"], sessionUuid)
                logs.put("开始答题：%s" % book_book.bookInfo.bookName)
                if not book_book.canTest:
                    logs.put("未到考试时间！")
                    continue
                for status in book_book.processProblems():
                    logs.put("回答问题：%s" % status["problem"])
                    logs.put("答题成功！" if status else "答题失败！")
                    logs.put("选择选项：%s"%status["trueAnswer"])
                logs.put("%s答题完成！" % book_book.bookInfo.bookName)

    logs.put("所有书籍答题完成！")
    logs.put("###LOG_SUCCESS###")
@main.route("/books",methods=['GET','POST'])
def books():
    thread =  threading.Thread(target=startBookProcess,args=(request.args.get("sessionUuid"),))
    thread.daemon = True
    thread.start()


    return render_template("books.html")
@main.route("/get_front_log/<sessionUuid>")
def get_front_log(sessionUuid):
    logs = log_session[sessionUuid]
    return jsonify(logs=logs.get() if not logs.empty() else "###UNDEFINED###")
