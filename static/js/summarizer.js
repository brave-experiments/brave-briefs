function showLoader() {
    const loader = document.querySelector('.loader')
    loader.style.display = 'block'
}

function hideLoader() {
    const loader = document.querySelector('.loader')
    loader.style.display = 'none'
}

function displaySummary(summary) {
  hideLoader()
  const summaryResults = document.getElementById("summary-results")
  summaryResults.innerHTML = ""

  let i = 0
  const typeSummary = () => {
    summaryResults.textContent += summary[i]
    i++
    if (i < summary.length) {
      setTimeout(typeSummary, 50)
    }
  }

  setTimeout(typeSummary, 50)
}

document.addEventListener("DOMContentLoaded", function() {
  const summarizeButton = document.querySelector('#summarize-button')
    summarizeButton.addEventListener('click', (e) => {
      e.preventDefault()

      const input = document.querySelector('#input')
      const text = input.value.trim()
      if (text !== '') {
          const isURL = text.match(/^https?:\/\//i)
          const data = {
              [isURL ? 'url' : 'text']: text
          }

          showLoader()

          fetch(isURL ? '/page' : '/summarize', {
              method: 'POST',
              body: JSON.stringify(data),
              headers: {
                  'Content-Type': 'application/json'
              }
          })
              .then(response => response.json())
              .then(data => {
                  displaySummary(data.summary)
              })
              .catch(error => console.error(error))
      }
  })
})
