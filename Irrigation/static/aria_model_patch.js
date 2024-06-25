
function radio_check(elbyname) {
  let elements = document.getElementsByName(elbyname);
  for (let i = 0; i < elements.length; i++) {
    let lab = 'check_' + elements[i].id + '';
    if (elements[i].value == "True") {
      elements[i].checked = true;
      document.getElementById(lab).innerText = 'On';
    }
    else {
      elements[i].checked = false;
      document.getElementById(lab).innerText = 'Off';
    }
  }
}

const area_status = async (area_ = '', radio = '') => {
  let url = '/irrigation/' + area_ + '/';
  let area_id = 'area_' + radio + area_;
  let status = document.getElementById(area_id).value;
  let lab_ = 'check_area_' + radio + area_;
  let data = {}

  if (status == "True") {
    data[radio] = false;
  }
  else if (status == "False") {
    data[radio] = true;
  }
  else {
    data[radio] = status;
  }

  if (radio == "schedule") {
    data[radio] = [Number(status) * 1800];
    alert(data[radio])
  }

  if (radio == "duration") {
    data[radio] = [Number(status) * 30];
    alert(data[radio])
  }

  const response = await fetch(url, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  let area_status = await response.json();
  if (typeof area_status[radio] == "boolean" && area_status[radio] == true) {
    document.getElementById(area_id).value = "True";
    document.getElementById(lab_).innerText = "On";
  }
  else if (typeof area_status[radio] == "boolean" && area_status[radio] == false) {
    document.getElementById(area_id).value = "False";
    document.getElementById(lab_).innerText = "Off";
  }
  return;
}
