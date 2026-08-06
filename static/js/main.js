const welcomeButton = document.querySelector("#welcome-button");
const welcomeMessage = document.querySelector("#welcome-message");

welcomeButton.addEventListener("click", function () {
    welcomeMessage.textContent = "Gracias por visitar Lasmondy Barber.";
});
