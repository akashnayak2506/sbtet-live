from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import concurrent.futures

app = Flask(__name__)
CORS(app)

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CONFIG = {

"20":{
"scheme":"9",
"sems":{
"1":"66",
"2":"71",
"3":"75",
"4":"78",
"5":"85",
"6":"91"
}
},

"21":{
"scheme":"9",
"sems":{
"1":"66",
"2":"71",
"3":"75",
"4":"78",
"5":"85",
"6":"91"
}
},

"22":{
"scheme":"9",
"sems":{
"1":"66",
"2":"71",
"3":"75",
"4":"78",
"5":"85",
"6":"91"
}
},

"23":{
"scheme":"9",
"sems":{
"1":"75",
"2":"78",
"3":"85",
"4":"91",
"5":"95",
"6":"95"
}
},

"24":{
"scheme":"11",
"sems":{
"1":"85",
"2":"91"
}
},

"25":{
"scheme":"11",
"sems":{
"1":"95"
}
}

}


def fetch_sem(pin, sem, exam, scheme):

    url = f"https://www.sbtet.telangana.gov.in/api/api/Results/GetStudentWiseReport?ExamMonthYearId={exam}&ExamTypeId=5&Pin={pin}&SchemeId={scheme}&SemYearId={sem}&StudentTypeId=1"

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            verify=False
        )

        if r.status_code != 200:
            return None

        data = r.json()

        if not data:
            return None

        return data[0]

    except:
        return None


@app.route('/api/fullreport', methods=['POST'])
def fullreport():

    req = request.json

    pin = req.get("pin", "").upper()

    batch = pin[:2]

    if batch not in CONFIG:

        return jsonify({
            "error": "Unsupported batch"
        })

    config = CONFIG[batch]

    semesters = []

    student_name = "Unknown"

    credits = 0

    for sem, exam in config["sems"].items():

        raw = fetch_sem(
            pin,
            sem,
            exam,
            config["scheme"]
        )

        if not raw:
            continue

        try:

            student_name = raw[
                "studentInfo"
            ][0].get(
                "StudentName",
                "Unknown"
            )

        except:
            pass

        try:

            info = raw[
                "studentSGPACGPAInfo"
            ][0]

            credits = (
                info.get("CgpaTotalCredits")
                or credits
            )

        except:
            pass

        subjects = []

        for s in raw.get(
            "studentWiseReport",
            []
        ):

            subjects.append({

                "subject":
                s.get(
                    "SubjectName",
                    "-"
                ),

                "m1":
                s.get(
                    "MID1_MARKS",
                    "-"
                ),

                "m2":
                s.get(
                    "MID2_MARKS",
                    "-"
                ),

                "internal":
                s.get(
                    "Internal_MARKS",
                    "-"
                ),

                "end":
                s.get(
                    "EndSemMarks",
                    "-"
                )

            })

        sem_sgpa = 0

        try:

            sem_sgpa = raw[
                "studentSGPACGPAInfo"
            ][0].get(
                "SGPA",
                0
            )

        except:
            pass

        semesters.append({

            "sem": sem,
            "subjects": subjects,
            "sgpa": sem_sgpa

        })

    return jsonify({

        "name": student_name,
        "pin": pin,
        "credits": credits,
        "semesters": semesters

    })


@app.route('/api/classresults', methods=['POST'])
def classresults():

    req = request.json

    pin = req.get("pin").upper()

    prefix = (
        pin.split("-")[0]
        + "-"
        + pin.split("-")[1]
        + "-"
    )

    def fetch_student(i):

        student_pin = (
            prefix +
            str(i).zfill(3)
        )

        try:

            batch = student_pin[:2]

            config = CONFIG[batch]

            raw = fetch_sem(
                student_pin,
                "1",
                config["sems"]["1"],
                config["scheme"]
            )

            if raw and raw.get("studentInfo"):

                name = raw[
                    "studentInfo"
                ][0].get(
                    "StudentName",
                    "Unknown"
                )

                sgpa = 0

                try:

                    sgpa = raw[
                        "studentSGPACGPAInfo"
                    ][0].get(
                        "SGPA",
                        0
                    )

                except:
                    pass

                return {

                    "rank": i,
                    "pin": student_pin,
                    "name": name,
                    "sgpa": sgpa

                }

        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:

        results = list(
            executor.map(
                fetch_student,
                range(1,71)
            )
        )

    students = [
        r for r in results
        if r
    ]

    return jsonify(students)


if __name__ == "__main__":

    import os

    print("SERVER STARTED")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
