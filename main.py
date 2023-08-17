from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup as bs4

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

class BoardResultFetcher:
    def __init__(self, url):
        self.url = url
    
    def get_html(self, roll_no, year):
        raise NotImplementedError("Subclasses must implement this method.")

class BiseGujrawala(BoardResultFetcher):
    def get_html(self, roll_no, year):
        payload = {
            'year': year,
            'class': 10,
            'rno': roll_no
        }
        res = requests.post(self.url, data=payload, headers=headers)
        return res.content

class BiseLahore(BoardResultFetcher):
    def get_html(self, roll_no, year):
        payload = {
            "__LASTFOCUS": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": '/wEPDwUKLTk0MzkxMjE2MWQYAQUJdHh0Rm9ybU5vDw88KwAHAGRk8YSAXXtYHiUo9Iz1lRqva7pJiZYxFCXWL9ODRTrj9Hw=',
            "__VIEWSTATEGENERATOR": "CA0B0334",
            "rdlistCourse": "SSC",
            "txtFormNo": roll_no,
            "ddlExamType": 2,
            "ddlExamYear": year,
            "Button1": "View Result"
        }
        response = requests.post(self.url, data=payload)
        return response.content

class BiseRawalpindi(BoardResultFetcher):
    def get_html(self, roll_no , year):
        result_url = self.url.format(roll_no , year)
        response = requests.get(result_url, headers=headers)
        return response.content

class ResultParser:
    def parse(self, html):
        raise NotImplementedError("Subclasses must implement this method.")

class BiseGujrawalaParser(ResultParser):
    def parse(self, html):
        soup = bs4(html, 'html.parser')

        divs = soup.findAll('div')[5:10]

        session = int(soup.findAll('h3')[1].text.split(' ')[-1])
        group = soup.find('h4').text.split(' ')[-1]

        roll_no, reg_no = [b.text for b in divs[0].findAll('b')]
        name, dob = [b.text for b in divs[1].findAll('b')]
        father_name, father_cnic = [b.text for b in divs[2].findAll('b')]
        school = " ".join(divs[3].findAll('b')[0].text.split(' ')[1:])

        table = soup.find('table', {'style': 'margin-bottom: 13px; border:none !important;'})
        rows = table.findAll('tr', {'height': "28"})
        total_marks = rows[8].findAll('td')[1].text.strip()
        obtained_marks = rows[8].findAll('td')[3].text.strip()

        subject_info = []
        for row in rows[:8]:
            columns = row.findAll('td')
            subject = columns[1].text.strip()
            max_marks = columns[2].text.strip()
            marks_1 = columns[3].text.strip()
            marks_2 = columns[4].text.strip()
            marks_p = columns[5].text.strip()
            max_obtained = columns[6].text.strip()
            percentage = columns[7].text.strip()
            s_grade = columns[8].text.strip()
            status_1 = columns[9].text.strip()
            status_2 = columns[10].text.strip()
            status_p = columns[11].text.strip()

            subject_data = {
                "total": max_marks,
                "practical": marks_p,
                "full_total": max_marks,
                "obtained_in_9th": marks_1,
                "status_in_9th": status_1,
                "obtained_in_10th": marks_2,
                "status_in_10th": status_2,
                "obtained_in_practical": marks_p,
                "status_in_practical": status_p,
                "total_obtained": max_obtained,
                "percentile_score": percentage,
                "grade": s_grade
            }
            subject_info.append({subject: subject_data})

        result = {
            "total": int(total_marks),
            "obtained": obtained_marks
        }

        student_info = {
            "roll_no": roll_no,
            "reg_no": reg_no,
            "session_info": session,
            "group": group,
            "name": name,
            "dob": dob,
            "father_name": father_name,
            "father_cnic": father_cnic,
            "institute": school,
            "marks": subject_info,
            "result": result
        }

        return student_info
    
class BiseLahoreParser(ResultParser):
    def get_student_info(self , table):
        roll_no = table.find("label",{"id" : "lblRollNoval"}).text
        reg_no = table.find("label",{"id" : "lblRegNum"}).text
        session_info = table.find("label",{"id" : "lblSession"}).text
        session_info.split(",")
        group = table.find("label" , {"id" : "lblGroup"}).text
        name = table.find("label",{"id" : "Name"}).text
        father_name = table.find("label",{"id" : "lblFatherName"}).text
        dob = table.find("label",{"id" : "lblDOB"}).text
        institution_district = table.find("label",{"id" : "lblExamCenter"}).text

        try:
          roll_no = int(roll_no)
        except:
          pass

        student_info = {"roll_no" : roll_no , "reg_no" : reg_no , "session_info" : session_info , "group" : group , "name" : name , 
                        "father_name" : father_name , "dob" : dob , "institution_district" : institution_district}
        return student_info

    def get_student_marks(self , subjects_marks):
        subjects_marks.pop(0) # Removing Extras
        subjects_marks.pop(0) # Removing Extras

        student_marks = {}

        for subject_data in subjects_marks:
          subject_data = subject_data.findAll("td")
          subject_name = subject_data[0].text
          subject_total_marks = subject_data[1].text
          subject_practical_marks = subject_data[2].text
          subject_total_marks_2 = subject_data[3].text
          subject_obtained_marks_1 = subject_data[4].text
          subject_obtained_marks_2 = subject_data[5].text
          subject_obtained_practical_marks = subject_data[6].text
          subject_obtained_total = subject_data[7].text
          subject_status = subject_data[8].text

          try:
            subject_obtained_practical_marks = int(subject_obtained_practical_marks)
          except:
            subject_obtained_practical_marks = None
          try:
            subject_practical_marks = int(subject_practical_marks)
          except:
            subject_practical_marks = None

          total_9 = int(subject_total_marks.split('+')[0])
          total_10 = int(subject_total_marks.split('+')[1].split('=')[0])
          full_total = total_10
          full_obtained = int(subject_obtained_marks_2)

          if subject_practical_marks:
            full_total += subject_practical_marks
            full_obtained += subject_obtained_practical_marks

          student_marks[subject_name] = {"9th" : {} , "10th" : {},"result" : {}}

          student_marks[subject_name]["9th"].update({
              "total" : total_9 , 
              "obtained" : int(subject_obtained_marks_1) ,
            }
          )

          student_marks[subject_name]["10th"].update({
              "total" : total_10 , 
              "practical" : subject_practical_marks , 
              "obtained" : int(subject_obtained_marks_2),
              "obtained_in_practical" : subject_obtained_practical_marks,
            }
          )

          student_marks[subject_name]["result"].update({
            "total" : int(subject_total_marks_2), 
            "obtained" : int(subject_obtained_total)
            })

        return student_marks

    def get_student_result(self, result):
        res_data = result.findAll('td')
        total = res_data[1].text
        result = res_data[2].text
        result = result.split("MARKS OBTAINED:")[1]
        status = result.split(' ')[0]
        obtained = result.split(' ')[1]
        grade = result.split(' ')[2]
        result = {
            "total" : int(total),
            "status" : status,
            "obtained" : int(obtained),
            "grade" : grade
          }
        return result

    def parse_html(self, html):
        soup = bs4(html,'html.parser')
        table = soup.find("table")
        student_data = soup.find("table",{"id" : "GridStudentData"})
        subjects_marks = student_data.findAll("tr")
        result = subjects_marks.pop()

        student_info = self.get_student_info(table)
        student_marks = self.get_student_marks(subjects_marks)
        student_result = self.get_student_result(result)

        student_info.update({
            "marks" : student_marks,
            "result" : student_result
        })

        return student_info

    def parse(self, html):
        return self.parse_html(html)

class BiseRawalpindiParser(ResultParser):
    def parse(self, html):
        soup = bs4(html,'html.parser')
        spans = soup.findAll("span")
        spans.pop(0)

        info = {"session_info": spans[0].text,
              "roll_no": int(spans[1].text),
              "name": spans[2].text,
              "student_type": spans[3].text,
              "status": spans[5].text,
              "form_id": spans[6].text
        }

        marks = {}
        headers = ["9th","10th","Practical","Status"]
        counter = 7
        while True:
          pre_counter = counter
          counter += 5
          if counter <= len(spans):
            marks[spans[pre_counter].text] = {headers[i]: j.text for i , j in enumerate(spans[pre_counter + 1 : counter])}
          else:
            break
        info.update({"marks" : marks})
        info.update({"result" : int(spans[4].text)})
        return info

class HtmlFetcher:
  def get_html(self , html_fetcher , roll_no , year):
    return html_fetcher.get_html(roll_no , year)

class DataProcessor:
  def get_result(self , data_processor , html):
    return data_processor.parse(html)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Construct HTML fetcher and result processor
html_fetcher = HtmlFetcher()
data_processor = DataProcessor()

bisegujrawala = BiseGujrawala("https://bisegrw.edu.pk/result-card-matric.html")
bisegujrawala_parser = BiseGujrawalaParser()

biselahore = BiseLahore("http://result.biselahore.com/")
biselahore_parser = BiseLahoreParser()

biserawalpindi = BiseRawalpindi("https://results.biserawalpindi.edu.pk/Result_Detail?p={}&q=2&r={}")
biserawalpindi_parser = BiseRawalpindiParser()

boards = ["biselahore","biserawalpindi",'bisegujrawala']

@app.get("/{board}/{roll_no}/{year}")
@app.get("/{board}/{roll_no}")
@app.get("/{roll_no}")
async def board_search(roll_no: str, board: str = 'biselahore' , year: int = 2023):
    board = board.lower()

    html = "html_fetcher.get_html({} , {}, {})"  # board , #roll_no , #year
    result = "data_processor.get_result({}_parser , {})"  # board , #html

    if board in boards:
        html = html.format(board, roll_no, year)
        html = eval(html)

        result = result.format(board, html)
        result = eval(result)

        return result
    else:
        return JSONResponse(content={"error": "Invalid board name"}, status_code=400)

@app.get(path="/")
async def developer_info():
  return  {
    "developer" : {"name" : "Kanwar Adnan","contact" : "kanwaradnanrajput@gmail.com"}
    }