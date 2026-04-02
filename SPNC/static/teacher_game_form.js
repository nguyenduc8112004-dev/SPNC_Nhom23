function showForm(){

    let type = document.getElementById("gameType").value

    let forms = document.querySelectorAll(".game-form")

    
    forms.forEach(f => f.style.display = "none")

    let questionBox = document.getElementById("questionBox")
    let xpBox = document.getElementById("xpBox")

    if(type == "quiz"){
        document.getElementById("quizForm").style.display = "block"
        updateOptions()
    }
    else if(type != "quiz"){

       
        questionBox.style.display = "block"
        xpBox.style.display = "block"

        
        let activeForm = document.getElementById(type + "Form")

        if(activeForm){
            activeForm.style.display = "block"
        }

    }else{

       
        questionBox.style.display = "none"
        xpBox.style.display = "none"
    }
}

function changeGameForm(){

let type =
document.getElementById("gameType").value

let form =
document.getElementById("gameForm")



if(type == "quiz"){

form.innerHTML = `

<label>Câu hỏi</label>
<input name="question">

<br><br>

<label>Phương án A</label>
<input name="A">

<label>Phương án B</label>
<input name="B">

<label>Phương án C</label>
<input name="C">

<label>Phương án D</label>
<input name="D">

<br><br>

<label>Đáp án đúng</label>

<select name="answer">
<option>A</option>
<option>B</option>
<option>C</option>
<option>D</option>
</select>

`

}



if(type == "fill"){

form.innerHTML = `

<label>Câu hỏi</label>
<input name="question">

<br><br>

<label>Đáp án</label>
<input name="answer">

`

}



if(type == "match"){

form.innerHTML = `

<h4>Cột trái</h4>

<input name="left1">
<input name="left2">

<h4>Cột phải</h4>

<input name="right1">
<input name="right2">

`

}


if(type == "order"){

form.innerHTML = `

<label>Dòng code 1</label>
<input name="line1">

<label>Dòng code 2</label>
<input name="line2">

`

}
}