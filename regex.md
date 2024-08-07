# tail expressions

ALL LOG: `tail -f log-trader-$(date +%Y%m%d).log`
BUY: `tail -f log-trader-$(date +%Y%m%d).log | grep -e "BUY ORDER " -e "was purchased" -e "stop"`
SELL: `tail -f log-trader-$(date +%Y%m%d).log | grep -e "SELL ORDER " -e "was sold" -e "stop"`
BUY/SELL: `tail -f log-trader-$(date +%Y%m%d).log | grep -e " ORDER " -e "was " -e "stop"`
CANCEL: `tail -f log-trader-$(date +%Y%m%d).log | grep -i -e "CANCEL"`

TO STOP: `touch stop`

