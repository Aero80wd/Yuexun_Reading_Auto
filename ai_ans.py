import os
from openai import OpenAI
import requests
class BailianModel:
    def __init__(self,modelName):
        self.modelName = modelName
        self.client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key="sk-xxxxx", # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.messages = []
    def setSystemRole(self,systemRole):
        self.messages.append({"role": "system", "content": systemRole})
    def ask(self,content):
        self.messages.append({"role": "user", "content": content})
        response = self.client.chat.completions.create(
            model=self.modelName,
            messages=self.messages,
        )
        self.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        print(response.choices[0].message.content)
        return response.choices[0].message.content
class BookInfo:
    def __init__(self,bookId,sessionuuid):
        req = requests.post("https://www.yuexunedu.com/store/api/v1.0/inquireReadingStudentBookDetailAccount.json",data={"bookId":bookId,"sessionUuid":sessionuuid,"appKey":"undefined"})
        rep = req.json()
        print(rep)
        if rep["status"] != "200":
            raise Exception("Request failed")
        self.bookName = rep["datas"][0]["bookName"]
        self.bookId = bookId
        self.pages = rep["datas"][0]["pageQty"]
        self.isRead = rep["datas"][0]["readingPage"] == rep["datas"][0]["pageQty"]
class ProblemOption:
    def __init__(self,optionContent,optionId):
        self.optionContent = optionContent
        self.optionId = optionId
class BookProblem:
    def __init__(self,problemJson):
        self.topicIdOption = []
        self.initProblemInfo(problemJson)
    def initProblemInfo(self,problemJson):
        self.paperUUID = problemJson["paperUuid"]
        self.topicId = problemJson["topicId"]
        self.topicContent = problemJson["topicTitle"]
        for option in problemJson["topicOptionList"]:
            self.topicIdOption.append(ProblemOption(option["content"],option["topicOptionId"]))
class Book:
    def __init__(self, bookId, sessionuuid):
        self.bookInfo = BookInfo(bookId,sessionuuid)
        self.sessionUUID = sessionuuid
        self.problems : list[BookProblem] = []
        self.client = BailianModel("qwen-plus")
        self.canTest = True
        self.client.setSystemRole("我将会问你几个关于《"+self.bookInfo.bookName+"》的问题，并给出每个选项和其对应的数字。请你根据问题和选项，给出对应的数字。且不要输出其他任何内容，只输出数字。\n例如题目：2024年是什么年？1145: 蛇年\n8686: 兔年\n114: 鸡年\n86: 兔年")
        self.initProblems()
    def initProblems(self):
        if not self.bookInfo.isRead:
            req = requests.post("https://www.yuexunedu.com/store/api/v1.0/updateReadingProgressAccount.json",data={"sessionUuid":self.sessionUUID,"appKey":"undefined","bookId":self.bookInfo.bookId,"readingPage":self.bookInfo.pages})
            rep = req.json()
            if rep["status"] != "200":
                raise Exception("Request failed")
        requests.post("https://www.yuexunedu.com/store/api/v1.0/inquireReadingTopicListGlobal.json",data={"bookId":self.bookInfo.bookId,"sessionUuid":self.sessionUUID,"appKey":"undefined"})
        req_prob = requests.post("https://www.yuexunedu.com/store/api/v1.0/generateReadingExamTopicAccount.json",data={"bookId":self.bookInfo.bookId,"sessionUuid":self.sessionUUID,"appKey":"undefined"})
        rep_prob = req_prob.json()

        if rep_prob["status"] != "200":
            print(rep_prob["message"])
            self.canTest = False
            return
        problems_json = rep_prob["datas"]



        for problem in problems_json:
            print(problem)
            self.problems.append(BookProblem(problem))
    def processProblems(self):
        for problem in self.problems:
            problem_string = problem.topicContent + "\n"
            for option in problem.topicIdOption:
                problem_string += str(option.optionId) + ": " + str(option.optionContent) + "\n"
            ans = self.client.ask(problem_string)
            judge_req = requests.post("https://www.yuexunedu.com/store/api/v1.0/judgeReadingExamTopicOptionAccount.json",data={"sessionUuid":self.sessionUUID,
                                                                                                                               "appKey":"undefined",
                                                                                                                               "paperUuid":problem.paperUUID,
                                                                                                                               "topicId":problem.topicId,
                                                                                                                               "topicOptionId":ans})
            if judge_req.json()["status"] != "200":
                yield False
            yield {"status": judge_req.json()["status"],"problem":problem_string,"trueAnswer":ans}

    