/* Cuenta regresiva de la pregunta. El servidor es quien manda: este script solo muestra
   el tiempo restante que calculó el servidor y envía el formulario cuando llega a cero. */
(function () {
  var raiz = document.getElementById("temporizador");
  var form = document.getElementById("form-pregunta");
  if (!raiz || !form) return;

  var total = parseFloat(raiz.dataset.total);
  var restante = parseFloat(raiz.dataset.restante);
  var fin = performance.now() + restante * 1000;
  var barra = document.getElementById("tiempo-barra");
  var texto = document.getElementById("tiempo-texto");
  var boton = document.getElementById("btn-responder");
  var enviado = false;

  function actualizar() {
    var r = Math.max(0, (fin - performance.now()) / 1000);
    barra.style.width = (r / total * 100) + "%";
    texto.textContent = Math.ceil(r);
    raiz.classList.toggle("urgente", r <= 10);

    if (r <= 0 && !enviado) {
      enviado = true;
      clearInterval(reloj);
      form.elements["tiempo_agotado"].value = "1";
      form.submit();              // si había una opción marcada se envía; si no, cuenta como errónea
    }
  }

  form.addEventListener("submit", function () {
    enviado = true;
    clearInterval(reloj);
    setTimeout(function () { boton.disabled = true; }, 0);
  });

  var reloj = setInterval(actualizar, 200);
  actualizar();
})();
