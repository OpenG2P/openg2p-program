document.addEventListener("DOMContentLoaded", function () {
    var mydata = JSON.parse(document.getElementById("pie_data").textContent);
    console.log(mydata);
    if (mydata.values[0] > 0 || mydata.values[1] > 0) {
        document.getElementById("chartContainer").innerHTML = "&nbsp;";
        document.getElementById("chartContainer").innerHTML =
            '<canvas id="myChart" width="500" height="500"></canvas>';
        var ctx = document.getElementById("myChart").getContext("2d");
        // eslint-disable-next-line no-undef,no-new
        new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: mydata.labels,
                datasets: [
                    {
                        data: mydata.values,
                        backgroundColor: ["#186ADE", "#76D0D9"],
                        borderColor: ["#186ADE", "#76D0D9"],
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                legend: {
                    display: true,
                    position: "bottom",
                },
                animation: {
                    animateScale: true,
                    animateRotate: true,
                },
            },
        });
    } else {
        const newElement = document.createElement("p");
        newElement.textContent = "In order to see the entitlements, please enroll into a program.";
        newElement.classList.add("no-payments-text");
        document.getElementById("chartContainer").innerHTML = "&nbsp;";
        document.getElementById("chartContainer").appendChild(newElement);
    }
});
