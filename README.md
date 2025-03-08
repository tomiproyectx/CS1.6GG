# Counter-Strike 1.6 Gungame Mode Project


## **CONTEXT**
Counter-Strike 1.6's GunGame (GG) mode is a fast-paced game type where players progress through a predefined set of weapons by securing kills. The first player to score a kill with the final weapon (usually a knife or grenade) wins the match.

While traditional leaderboards rank players based on total kills or playtime, this project introduces a statistically driven ranking system that considers multiple performance metrics. The goal is to provide better insights into player skills, aid in team formation for tournaments, and help players analyze and improve their gameplay.

## **PROJECT SUMMARY**
This project automates the daily extraction, transformation, and processing of leaderboard data from a Counter-Strike 1.6 GunGame server. The extracted data is used to create an enhanced ranking system based on statistical analysis, providing deeper insights into player performance. This system helps with team selection for tournaments, individual skill assessment, and player behavior analysis, offering a more strategic approach to in-game decision-making.

## 🛠 Tools & Technologies Used

| Tool | Purpose |
|------|---------|
| **Python** | Web scraping (**BeautifulSoup**), data processing (**Pandas**), and database integration (**SQLite3**) |
| **SQLite** | Storing and querying extracted leaderboard data |
| **Windows Task Scheduler** | Automating the daily execution of the data pipeline |
| **Power BI** | Visualizing player performance and ranking insights |
| **SQL** | Database schema creation, transformations, and ranking calculations |


## PROJECT WALKTHROUGH

### Data Flow Diagram:

![Data Flow Diagram](https://github.com/tomiproyectx/CS1.6GG/blob/main/DFD%20Diagram%20CS16GGTP%20V2.png)


## 📂 Project Walkthrough  
This project follows an **ETL workflow**, which consists of:  

### **1️⃣ Extraction (Getting the Data)**  
- A **Python script** runs **daily** to extract player statistics from a Counter-Strike 1.6 GunGame leaderboard.  
- The data is stored in an **SQLite database** as raw, unprocessed data (`RAW` table).  
- A **backup of the raw dataset** is created for historical tracking.  

### **2️⃣ Transformation (Cleaning & Structuring Data)**  
- The script processes the extracted data, ensuring **no duplicates** are inserted.  
- A **new version of the leaderboard (`CURATED` table)** is created, filtering only the latest, updated records.  
- Players who **haven’t played recently are excluded** to maintain an up-to-date dataset.  

### **3️⃣ Loading & Ranking Calculation (Building the Final Leaderboard)**  
- The original leaderboard ranked players based on **total points**, which favored players with the most time played.  
- To **fix this**, a new ranking system (`REFINED` table) was created that evaluates **player impact based on performance, not playtime**.  
- The ranking formula considers **accuracy, headshot ratio, kill-death-assist (KDA) ratio, and damage per time played**.  

👉 This ensures that **skilled players are properly ranked, not just those who play longer**.  

---

## **🏆 The New Leaderboard**  
**Before:**  
🔹 Players with the **most time played** ranked highest.  
🔹 Hard to evaluate **true player skill**.  

**After:**  
✅ **Skill-based ranking**, using advanced statistical calculations.  
✅ **More competitive and fair ranking system** for tournaments.  
✅ Helps **players analyze their performance** and improve gameplay.  
