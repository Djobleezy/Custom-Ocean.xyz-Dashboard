# Ocean.xyz Bitcoin Mining Dashboard

## A Retro Mining Monitoring Solution

This open-source dashboard provides real-time monitoring for Ocean.xyz pool miners, offering detailed insights on hashrate, profitability, worker status, and network metrics. Designed with a retro terminal aesthetic and focused on reliability, it helps miners maintain complete oversight of their operations.

---
## Gallery:
![config](https://github.com/user-attachments/assets/ec6ebeae-569f-48a9-9437-0354940422c1)
![dashboard](https://github.com/user-attachments/assets/1042b586-7f02-4514-83f6-1fee50c38b18)
![workers](https://github.com/user-attachments/assets/2d26dbd0-64b7-4f77-921c-c48ad2cb6122)
![blocks](https://github.com/user-attachments/assets/e38d6f17-5e89-4560-aeec-69a349fa12ba)
![notifications](https://github.com/user-attachments/assets/2819b2d2-5e4a-45e8-8fa2-2d5daf285e27)

---

## Key Features


### Real-Time Mining Metrics
- **Live Hashrate Tracking**: Monitor 60-second, 10-minute, 3-hour, and 24-hour average hashrates
- **Profitability Analysis**: View daily and monthly earnings in both BTC and USD
- **Financial Calculations**: Automatically calculate revenue, power costs, and net profit
- **Network Statistics**: Track current Bitcoin price, difficulty, and network hashrate
- **Payout Monitoring**: View unpaid balance and estimated time to next payout
- **Pool Fee Analysis**: Monitor pool fee percentages with visual indicator when optimal rates (0.9-1.3%) are detected


### Worker Management
- **Fleet Overview**: Comprehensive view of all mining devices in one interface
- **Status Monitoring**: Real-time status indicators for online and offline devices
- **Performance Data**: Individual hashrate, temperature, and acceptance rate metrics
- **Filtering Options**: Sort and search by device type or operational status

### Bitcoin Block Explorer
- **Recent Blocks**: View the latest blocks added to the blockchain
- **Block Details**: Examine transaction counts, fees, and mining pool information
- **Visual Indicators**: Track network difficulty and block discovery times

### System Resilience
- **Connection Recovery**: Automatic reconnection after network interruptions
- **Backup Polling**: Fallback to traditional polling if real-time connection fails
- **Cross-Tab Synchronization**: Data consistency across multiple browser tabs
- **Server Health Monitoring**: Built-in watchdog processes ensure reliability

### Distinctive Design Elements
- **Retro Terminal Aesthetic**: Nostalgic interface with modern functionality
- **Boot Sequence Animation**: Engaging initialization sequence on startup
- **System Monitor**: Floating status display with uptime and refresh information
- **Responsive Interface**: Adapts to desktop and mobile devices

## Quick Start

### Installation

1. Clone the repository
   ```
   git clone https://github.com/Djobleezy/Custom-Ocean.xyz-Dashboard.git
   cd Custom-Ocean.xyz-Dashboard
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the setup script:
   ```
   python setup.py
   ```

4. Configure your mining settings in [config.json](https://github.com/Djobleezy/Custom-Ocean.xyz-Dashboard/blob/main/config.json):
   ```json
   {
     "power_cost": 0.12,
     "power_usage": 3450,
     "wallet": "yourwallethere"  <--- make sure to replace this value in all project files (boot.html, app.py, config.py, config.json, & setup.py)
   }
   ```

5. Start the application:
   ```
   python App.py
   ```

6. Open your browser at `http://localhost:5000`

For detailed deployment instructions with Redis persistence and Gunicorn configuration, see [deployment_steps.md](deployment_steps.md).

## Using docker-compose (with Redis)

The `docker-compose.yml` file makes it easy to deploy the dashboard and its dependencies.

### Steps to Deploy

1. **Start the services**:
   Run the following command in the project root:
   ```
   docker-compose up -d
   ```

2. **Access the dashboard**:
   Open your browser at `http://localhost:5000`.

3. **Stop the services**:
   To stop the services, run:
   ```
   docker-compose down
   ```
### Customization

You can modify the following environment variables in the `docker-compose.yml` file:
- `WALLET`: Your Bitcoin wallet address.
- `POWER_COST`: Cost of power per kWh.
- `POWER_USAGE`: Power usage in watts.

Redis data is stored in a persistent volume (`redis_data`), and application logs are saved in the `./logs` directory.

For more details, refer to the [docker-compose documentation](https://docs.docker.com/compose/).

## Dashboard Components

### Main Dashboard

- Interactive hashrate visualization with trend analysis
- Real-time profitability metrics with cost calculations
- Network statistics with difficulty and price tracking
- Payout information with estimation timing
- Visual indicators for metric changes

### Workers Dashboard

- Fleet summary with aggregate statistics
- Individual worker cards with detailed metrics
- Status indicators with color-coded alerts
- Search and filtering functionality
- Performance trend mini-charts

### Blocks Explorer

- Recent block visualization with mining details
- Transaction statistics and fee information
- Mining pool attribution
- Block details modal with comprehensive data

### System Monitor

- Floating interface providing system statistics
- Progress indicator for data refresh cycles
- System uptime display
- Real-time connection status

## System Requirements

The application is designed for efficient resource utilization:
- **Server**: Any system capable of running Python 3.9+
- **Memory**: Minimal requirements (~100MB RAM)
- **Storage**: Less than 50MB for application files
- **Database**: Optional Redis for persistent state
- **Compatible with**: Windows, macOS, and Linux

## Technical Architecture

Built with a modern stack for reliability and performance:
- **Backend**: Flask with Server-Sent Events for real-time updates
- **Frontend**: Vanilla JavaScript with Chart.js for visualization
- **Data Processing**: Concurrent API calls with smart caching
- **Resilience**: Automatic recovery mechanisms and state persistence
- **Configuration**: Environment variables and JSON-based settings

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
bitcoin-mining-dashboard/
│
├── App.py                      # Main application entry point
├── config.py                   # Configuration management
├── config.json                 # Configuration file
├── data_service.py             # Service for fetching mining data
├── models.py                   # Data models
├── state_manager.py            # Manager for persistent state
├── worker_service.py           # Service for worker data management
├── setup.py                    # Setup script for organizing files
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template with common elements
│   ├── boot.html              # Boot sequence animation
│   ├── dashboard.html         # Main dashboard template
│   ├── workers.html           # Workers dashboard template
│   ├── blocks.html            # Bitcoin blocks template
│   └── error.html             # Error page template
│
├── static/                     # Static assets
│   ├── css/                   # CSS files
│   │   ├── common.css         # Shared styles across all pages
│   │   ├── dashboard.css      # Main dashboard styles
│   │   ├── workers.css        # Workers page styles
│   │   ├── boot.css           # Boot sequence styles
│   │   ├── blocks.css         # Blocks page styles
│   │   ├── error.css          # Error page styles
│   │   └── retro-refresh.css  # Floating refresh bar styles
│   │
│   └── js/                    # JavaScript files
│       ├── main.js            # Main dashboard functionality
│       ├── workers.js         # Workers page functionality
│       ├── blocks.js          # Blocks page functionality
│       ├── block-animation.js # Block mining animation
│       └── BitcoinProgressBar.js # System monitor functionality
│
├── deployment_steps.md         # Deployment guide
└── project_structure.md        # Additional structure documentation
```

For more detailed information on the architecture and component interactions, see [project_structure.md](project_structure.md).

## Troubleshooting

For optimal performance:

1. Ensure your wallet address is correctly configured
2. Check network connectivity for consistent updates
3. Use the system monitor to verify connection status
4. Access the health endpoint at `/api/health` for diagnostics
5. For stale data issues, use the Force Refresh function

## License

Available under the MIT License. This is an independent project not affiliated with Ocean.xyz.

## Acknowledgments

- Ocean.xyz mining pool for their service
- mempool.guide
- The open-source community for their contributions
- Bitcoin protocol developers
