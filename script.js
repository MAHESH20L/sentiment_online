let globalData = null;


// ================= LINK CONVERTER =================
function convertToDirectCSV(url){

    // Google Drive
    if(url.includes("drive.google.com")){
        const match = url.match(/\/d\/(.*?)\//);
        if(match){
            return `https://drive.google.com/uc?export=download&id=${match[1]}`;
        }
    }

    // GitHub
    if(url.includes("github.com")){
        return url
            .replace("github.com","raw.githubusercontent.com")
            .replace("/blob/","/");
    }

    // Dropbox
    if(url.includes("dropbox.com")){
        return url.replace("?dl=0","?dl=1");
    }

    return url;
}


// ================= UPLOAD =================
async function uploadCSV(){

    const fileInput = document.getElementById("csvFile");
    const file = fileInput.files[0];

    const csvLink = document.getElementById("csvLink").value;

    if(!file && !csvLink){
        alert("Upload CSV or paste CSV link");
        return;
    }

    document.getElementById("loading").style.display="block";

    let res;

    try{

        // ===== FILE UPLOAD =====
        if(file){

            const formData = new FormData();
            formData.append("file", file);

            res = await fetch("https://pattimanim-sentiment.hf.space/predict-csv",{
                method:"POST",
                body:formData
            });

        }

        // ===== CSV LINK =====
        else if(csvLink){

            const directLink = convertToDirectCSV(csvLink);

            res = await fetch("https://pattimanim-sentiment.hf.space/predict-csv-link",{
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body: JSON.stringify({
                    url: directLink
                })
            });

        }

        const data = await res.json();

        console.log("API RESPONSE:", data);

        document.getElementById("loading").style.display="none";

        if(data.error){
            alert(data.error);
            return;
        }

        globalData = data;

        buildTable();
        buildCharts();
        buildReco();

    }
    catch(err){
        console.error(err);
        document.getElementById("loading").style.display="none";
        alert("Failed to fetch CSV");
    }

}


// ================= TABLE =================
function buildTable(){

    if(!globalData || !globalData.results){
        console.error("Results missing", globalData);
        return;
    }

    let html=`<div class="section-card">
    <h2>📄 Sentiment Results</h2>
    <table>
    <tr>
    <th>Tweet</th>
    <th>Topic</th>
    <th>Sentiment</th>
    <th>Confidence</th>
    </tr>`;

    globalData.results.forEach(r=>{
        html+=`<tr>
        <td>${r.tweet}</td>
        <td>${r.topic}</td>
        <td>${r.sentiment}</td>
        <td>${r.confidence}</td>
        </tr>`;
    });

    html+="</table></div>";

    document.getElementById("tableSection").innerHTML = html;
}


// ================= CHARTS =================
function buildCharts(){

    if(!globalData){
        return;
    }

    let html = `
    <div class="section-card" id="pdfContent">

    <h1 style="text-align:center;">AI Sentiment Analysis Report</h1>

    <h2>📊 Overall Sentiment</h2>
    <img src="data:image/png;base64,${globalData.overall_sentiment_chart}">

    <h2>📊 Topic-wise Sentiment</h2>
    <img src="data:image/png;base64,${globalData.topic_sentiment_chart}">
    <h2>🚨 Top Negative Issues</h2>
    <img src="data:image/png;base64,${globalData.negative_topics_chart}">

    <h2>🧠 AI Recommendations</h2>
    `;

    globalData.recommendations.forEach(r=>{
        html += `<p>👉 ${r}</p>`;
    });

    html += `
    <h2>📄 Sentiment Results</h2>
    <table border="1" style="width:100%;border-collapse:collapse;">
    <tr>
    <th>Tweet</th>
    <th>Topic</th>
    <th>Sentiment</th>
    <th>Confidence</th>
    </tr>`;

    globalData.results.forEach(r=>{
        html += `<tr>
        <td>${r.tweet}</td>
        <td>${r.topic}</td>
        <td>${r.sentiment}</td>
        <td>${r.confidence}</td>
        </tr>`;
    });

    html += `</table></div>`;

    document.getElementById("chartSection").innerHTML = html;
}


// ================= RECOMMENDATIONS =================
function buildReco(){

    if(!globalData){
        return;
    }

    let html = `<div class="section-card"><h2>🧠 AI Recommendations</h2>`;

    globalData.recommendations.forEach(r=>{
        html += `<p>👉 ${r}</p>`;
    });

    html += "</div>";

    document.getElementById("recoSection").innerHTML = html;
}


// ================= NAVIGATION =================
function showHome(){

    document.getElementById("chartSection").style.display="none";
    document.getElementById("recoSection").style.display="none";
    document.getElementById("tableSection").style.display="block";

}

function showCharts(){

    document.getElementById("chartSection").style.display="block";
    document.getElementById("recoSection").style.display="none";
    document.getElementById("tableSection").style.display="none";

}

function showReco(){

    document.getElementById("chartSection").style.display="none";
    document.getElementById("recoSection").style.display="block";
    document.getElementById("tableSection").style.display="none";

}


// ================= PDF DOWNLOAD =================
function downloadPDF(){

    const element = document.getElementById("pdfContent");

    if(!element){
        alert("Upload CSV first");
        return;
    }

    html2pdf().from(element).save("AI_Sentiment_Report.pdf");

}
