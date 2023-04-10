var btn = document.querySelector('.add');
var cohortstrbox = document.getElementById("cohorts");
var ul = document.querySelector('ul');
 
function dragStart(e) {
  this.style.opacity = '0.4';
  dragSrcEl = this;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/html', this.innerHTML);
};
 
function dragEnter(e) {
  this.classList.add('over');
}
 
function dragLeave(e) {
  e.stopPropagation();
  this.classList.remove('over');
}
 
function dragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  return false;
}
 
function dragDrop(e) {
  if (dragSrcEl != this) {
    dragSrcEl.innerHTML = this.innerHTML;
    this.innerHTML = e.dataTransfer.getData('text/html');
  }
  return false;
}
 
function dragEnd(e) {
    var listItens = document.querySelectorAll('.draggable');
    [].forEach.call(listItens, function(item) {
        item.classList.remove('over');
    });
    this.style.opacity = '1';
    var s = [];
    for(var i=0;i<listItens.length;i++) {
      let item = listItens[i];
      s.push(item.querySelector("span").innerHTML);
      item.querySelector("i").addEventListener('click', function (event) {
         console.log("item clicked");
         try{
             ul.removeChild(item);
         }catch(err) {
             console.log(err)
         }
      });
    }
    cohortstrbox.value = s.join(",");
    console.log(cohortstrbox.value)
}
 
function addEventsDragAndDrop(el) {
  el.addEventListener('dragstart', dragStart, false);
  el.addEventListener('dragenter', dragEnter, false);
  el.addEventListener('dragover', dragOver, false);
  el.addEventListener('dragleave', dragLeave, false);
  el.addEventListener('drop', dragDrop, false);
  el.addEventListener('dragend', dragEnd, false);
}
 
var listItens = document.querySelectorAll('.draggable');
[].forEach.call(listItens, function(item) {
  addEventsDragAndDrop(item);
});
 
function addNewItem() {
  var newItem = document.querySelector('.input').value;
  if (newItem != '') {
    document.querySelector('.input').value = '';
    var li = document.createElement('li');
    var attr = document.createAttribute('draggable');
    li.className = 'draggable';
    attr.value = 'true';
    li.setAttributeNode(attr);
    var span = document.createElement('span');
    span.appendChild(document.createTextNode(newItem));
    li.appendChild(span);
    var ii = document.createElement('i');
    ii.className = 'del';
    ii.addEventListener('click', function (event) {
        console.log("ii clicked");
        ul.removeChild(li);
    });
    li.appendChild(ii);
    ul.appendChild(li);
    addEventsDragAndDrop(li);
    
    var listItens = document.querySelectorAll('.draggable');
    var s = [];
    for(var i=0;i<listItens.length;i++) {
      let item = listItens[i];
      s.push(item.querySelector("span").innerHTML);
    }
    cohortstrbox.value = s.join(",");
    console.log(cohortstrbox.value)
    window.scrollTo(0,document.body.scrollHeight);
  }
}
 
btn.addEventListener('click', addNewItem);

var inputBox = document.querySelector('.input');
inputBox.addEventListener("keyup", function(event) {
  if (event.keyCode === 13) {
      event.preventDefault();
      addNewItem();
  }
});







































