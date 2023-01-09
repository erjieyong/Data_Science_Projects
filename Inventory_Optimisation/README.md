# Inventory Optimisation through optimising safety stock, economic order quantity and reorder point

**Streamlit link**: [https://erjieyong-data-scien-inventory-optimisationstreamlit-app-ie6zc6.streamlit.app/](https://erjieyong-data-science-p-inventory-optimisationdashboard-slaxc3.streamlit.app/)

## Problem Statement
There are inventories valued in the billions sitting around the world idling and collecting dust because of improper planning. Not only are there opportunity costs tied up to procure these unnecessary inventory, there are also active recurrent costs such warehouse space, handling cost, utilities costs involved to maintain and house these inventory. Hence, there's an entire field of research centered around supply chain optimisation. In our scenario, we are looking at purchasing inventory optimisation that could potentially save companies millions of dollars.

# Background
We are optimising 3 aspects of the purchased inventory

## Safety Stock
Safety stock (SS) is simply extra inventory held by a company in case demand increases unexpectedly. This means it’s additional stock above the desired inventory level that you would usually hold for day-to-day operations. One of the main reasons that companies implement a safety stock strategy is to prevent stockouts. Stockouts are usually caused by:
- Changes in consumer demand
- Incorrect stock forecasts
- Variability in lead times for raw materials

We are particularly interested in safety stocks calculation that takes into account uncertain demand and lead time (both independent of each other). The formula is as such:

SS = Z $\times$ $\sqrt{(x̄_{leadtime} \times σ_{demand}^2) + (x̄_{demand}^2 \times σ_{leadtime}^2)}$

## Economic Order Quantity
Economic order quantity (EOQ) refers to the ideal order quantity a company should purchase in order to minimize its inventory costs, such as holding costs, shortage costs, and order costs

The formula for calculating EOQ is as such:

EOQ = $\sqrt{(2 \times HandlingCost_{per shipment} \times x̄_{demand/year}) / HoldingCost_{unit/year}}$

## Reorder point
Reorder point (ROP) is the minimum inventory level a specific product can reach before a company is prompted to order more inventory based on the EOQ

The formula for calculating ROP is as such:

ROP = SS + $x̄_{demand}$ $\times$  $x̄_{leadtime}$

# Modeling and Deployment
Data cleaning is first done on the historical data. These cleaned variables are then subsequently fed into the different formula for SS, EOQ and ROP. Finally, the output are presented on streamlit upon user's selection of the different variables.

Users may also choose to fine tune the different variables to further explore the implications of how various variables may impact the SS, EOQ and ROP.

# Further Evaluation
 - Consider a combination of various SKUs being fitted into a container for further optimisation
 - Calculate the total supply chain costs for all SKUs across different hubs

# References
- [https://web.mit.edu/2.810/www/files/readings/King_SafetyStock.pdf](https://web.mit.edu/2.810/www/files/readings/King_SafetyStock.pdf)
- [https://www.investopedia.com/ask/answers/052715/how-economic-order-quantity-model-used-inventory-management.asp](https://www.investopedia.com/ask/answers/052715/how-economic-order-quantity-model-used-inventory-management.asp)
- [https://www.inflowinventory.com/blog/reorder-point-formula-safety-stock/](https://www.inflowinventory.com/blog/reorder-point-formula-safety-stock/)
