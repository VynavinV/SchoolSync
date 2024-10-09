document.addEventListener('DOMContentLoaded', function () {
    const dateElement = document.getElementById('date');
    const currentDate = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const newsRssUrl = 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'; // Example NY Times RSS URL
    const dealsRssUrl = 'https://www.redflagdeals.com/rss/category/hot-deals/'; // Example deals RSS URL
    const holidaysUrl = 'https://date.nager.at/api/v2/PublicHolidays/2024/CA';
    const newsTickerContainer = document.getElementById('news-ticker-container');
    const dealsTickerContainer = document.getElementById('deals-ticker-container');
    const holidaysList = document.getElementById('holidays-list');
    const cityInput = document.querySelector(".city-input");
    const searchButton = document.querySelector(".search-btn");
    const locationButton = document.querySelector(".location-btn");
    const currentWeatherDiv = document.querySelector(".current-weather");
    const weatherCardsDiv = document.querySelector(".weather-cards");
    const API_KEY = "697f9b8afed2a6d55f0743ff8ac3feda"; // API key for OpenWeatherMap API

    // Function to fetch RSS feed and parse items
    function fetchRssFeed(url) {
        return fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok ${response.statusText}`);
                }
                return response.text();
            })
            .then(data => {
                const parser = new DOMParser();
                const xml = parser.parseFromString(data, 'application/xml');
                const items = xml.querySelectorAll('item');
                const headlines = [];
                items.forEach(item => {
                    const title = item.querySelector('title').textContent;
                    const description = item.querySelector('description').textContent;
                    const link = item.querySelector('link').textContent;
                    headlines.push({ title, description, link });
                });
                return headlines;
            })
            .catch(error => {
                console.error(`Error fetching RSS feed from ${url}:`, error);
                return [];
            });
    }

    // Function to display headlines in a ticker
    function displayTicker(container, headlines) {
        let currentIndex = 0;

        function showHeadline() {
            container.innerHTML = '';
            const headline = headlines[currentIndex];
            const tickerItem = document.createElement('div');
            tickerItem.className = 'ticker-item active';
            tickerItem.innerHTML = `<a href="${headline.link}" target="_blank">${headline.title}: ${headline.description}</a>`;
            container.appendChild(tickerItem);

            setTimeout(() => {
                tickerItem.classList.remove('active');
                currentIndex = (currentIndex + 1) % headlines.length;
                showHeadline();
            }, 5000); // Change headline every 15 seconds
        }

        if (headlines.length > 0) {
            showHeadline();
        } else {
            container.innerHTML = `<h1>No headlines found</h1>`;
        }
    }

    // Fetch upcoming Canadian holidays
    fetch(holidaysUrl)
        .then(response => response.json())
        .then(data => {
            const now = new Date();
            const upcomingHolidays = data.filter(holiday => new Date(holiday.date) >= now);
            const holidays = upcomingHolidays.slice(0, 10); // Get only the first 10 upcoming holidays
            holidays.forEach(holiday => {
                const holidayItem = document.createElement('li');
                holidayItem.textContent = `${holiday.date} - ${holiday.localName}`;
                holidaysList.appendChild(holidayItem);
            });
        })
        .catch(error => {
            holidaysList.innerHTML = `<li>Error fetching holidays</li>`;
            console.error('Error fetching holidays:', error);
        });

    // Clock Functionality
    function updateClock() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // The hour '0' should be '12'
        const timeString = `${hours}:${minutes}:${seconds} ${ampm}`;
        document.getElementById('Clock').textContent = timeString;
    }

    setInterval(updateClock, 1000);
    updateClock();
    dateElement.textContent = currentDate.toLocaleDateString(undefined, options);

    // Fetch and display news headlines
    fetchRssFeed(newsRssUrl).then(headlines => displayTicker(newsTickerContainer, headlines));

    // Fetch and display deals headlines
    fetchRssFeed(dealsRssUrl).then(headlines => displayTicker(dealsTickerContainer, headlines));
    const daysTag = document.querySelector(".days"),
prevNextIcon = document.querySelectorAll(".icons span");

// getting new date, current year and month
let date = new Date(),
currYear = date.getFullYear(),
currMonth = date.getMonth();

// storing full name of all months in array
const months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"];

const renderCalendar = () => {
    let firstDayofMonth = new Date(currYear, currMonth, 1).getDay(), // getting first day of month
    lastDateofMonth = new Date(currYear, currMonth + 1, 0).getDate(), // getting last date of month
    lastDayofMonth = new Date(currYear, currMonth, lastDateofMonth).getDay(), // getting last day of month
    lastDateofLastMonth = new Date(currYear, currMonth, 0).getDate(); // getting last date of previous month
    let liTag = "";

    for (let i = firstDayofMonth; i > 0; i--) { // creating li of previous month last days
        liTag += `<li class="inactive">${lastDateofLastMonth - i + 1}</li>`;
    }

    for (let i = 1; i <= lastDateofMonth; i++) { // creating li of all days of current month
        // adding active class to li if the current day, month, and year matched
        let isToday = i === date.getDate() && currMonth === new Date().getMonth() 
                     && currYear === new Date().getFullYear() ? "active" : "";
        liTag += `<li class="${isToday}">${i}</li>`;
    }

    for (let i = lastDayofMonth; i < 6; i++) { // creating li of next month first days
        liTag += `<li class="inactive">${i - lastDayofMonth + 1}</li>`
    }
    currentDate.innerText = `${months[currMonth]} ${currYear}`; // passing current mon and yr as currentDate text
    daysTag.innerHTML = liTag;
}
renderCalendar();

prevNextIcon.forEach(icon => { // getting prev and next icons
    icon.addEventListener("click", () => { // adding click event on both icons
        // if clicked icon is previous icon then decrement current month by 1 else increment it by 1
        currMonth = icon.id === "prev" ? currMonth - 1 : currMonth + 1;

        if(currMonth < 0 || currMonth > 11) { // if current month is less than 0 or greater than 11
            // creating a new date of current year & month and pass it as date value
            date = new Date(currYear, currMonth, new Date().getDate());
            currYear = date.getFullYear(); // updating current year with new date year
            currMonth = date.getMonth(); // updating current month with new date month
        } else {
            date = new Date(); // pass the current date as date value
        }
        renderCalendar(); // calling renderCalendar function
    });
});
});
