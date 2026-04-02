document.addEventListener('DOMContentLoaded', () => {
    // Set current date
    const dateElement = document.getElementById('current-date');
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = now.toLocaleDateString('en-US', options);

    // Function to fetch the Offer of the Day
    async function fetchOfferOfDay() {
        try {
            const response = await fetch('/api/v1/offer-of-the-day');
            if (response.ok) {
                const data = await response.json();
                updateOfferUI(data);
            }
        } catch (error) {
            console.error('Error fetching offer:', error);
        }
    }

    function updateOfferUI(data) {
        const title = document.getElementById('offer-title');
        const desc = document.getElementById('offer-description');
        const erv = document.querySelector('.erv-badge');
        const category = document.querySelector('.category-badge');

        title.textContent = data.title;
        desc.textContent = data.description;
        erv.textContent = `ERV: $${data.erv.toFixed(2)}`;
        category.textContent = data.category;
    }

    // Button interactions
    const applyBtn = document.getElementById('btn-apply');
    const dismissBtn = document.getElementById('btn-dismiss');

    applyBtn.addEventListener('click', () => {
        alert('Executing Financial Winning Move...');
    });

    dismissBtn.addEventListener('click', () => {
        const container = document.getElementById('offer-of-the-day-container');
        container.style.opacity = '0';
        setTimeout(() => {
            container.style.display = 'none';
        }, 300);
    });

    // Initial fetch
    fetchOfferOfDay();
});
