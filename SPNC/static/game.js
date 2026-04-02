
function submitQuiz(id, correct, xp){

let selected =
document.querySelector(
`input[name="quiz${id}"]:checked`
)

if(!selected){
alert("Chọn đáp án!")
return
}

let isCorrect = selected.value == correct

if(isCorrect){
alert("Đúng!")
}else{
alert("Sai!")
}

fetch("/submit_game",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body: JSON.stringify({
game_id:id,
xp:xp,
correct:isCorrect
})
})

}

function sendXP(game_id, xp){

fetch("/submit_game",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body: JSON.stringify({
game_id: game_id,
xp: xp
})

})

.then(response => response.json())

.then(data => {

alert(data.message)

})

.catch(error => {

console.log(error)

alert("Server error")

})

}





function checkQuiz(correct){

let selected =
document.querySelector(
'input[name^="quiz"]:checked'
)

if(!selected){
alert("Chọn đáp án!")
return
}

if(selected.value == correct){
alert("Đúng! +XP 🎉")
}else{
alert("Sai rồi!")
}

}





function checkFill(correct, game_id){

let answer =
document.getElementById("fill").value

if(answer.trim().toLowerCase() == correct.toLowerCase()){

sendXP(game_id,10)

}else{

alert("Try again")

}

}





function checkMatch(game_id){

let a =
document.getElementById("match1").value

let b =
document.getElementById("match2").value

if(a == "loop" && b == "exit"){

sendXP(game_id,20)

}else{

alert("Wrong Matching")

}

}





function checkOrder(game_id){

let line1 =
document.getElementById("line1").value

let line2 =
document.getElementById("line2").value

if(line1 == "for" && line2 == "print"){

sendXP(game_id,20)

}else{

alert("Wrong order")

}

}

function sendXP(game_id, xp){

fetch("/submit_game", {
    method:"POST",
    headers:{
        "Content-Type":"application/json"
    },
    body: JSON.stringify({
        game_id: game_id,
        xp: xp
    })
})
.then(res=>res.json())
.then(data=>{
    alert(data.message)
})

}