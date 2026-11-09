(function () {
  document.body.classList.remove("sem-js");

  document.querySelectorAll("form[data-envio-unico]").forEach(function (form) {
    var enviando = false;
    form.addEventListener("submit", function (event) {
      if (enviando) {
        event.preventDefault();
        return;
      }
      enviando = true;
      var botao = event.submitter || form.querySelector("[type='submit']");
      window.setTimeout(function () {
        if (!botao) {
          return;
        }
        botao.disabled = true;
        if (botao.getAttribute("data-aguarde")) {
          botao.textContent = botao.getAttribute("data-aguarde");
        }
      }, 0);
    });
  });

  document.querySelectorAll("[data-imprimir]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      window.print();
    });
  });

  document.querySelectorAll("[data-copiar]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var texto = botao.getAttribute("data-copiar") || "";
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        botao.textContent = "Selecione o número acima";
        return;
      }
      navigator.clipboard.writeText(texto).then(function () {
        botao.textContent = "Número copiado";
      }).catch(function () {
        botao.textContent = "Selecione o número acima";
      });
    });
  });
})();
