from bagbag import *

if __name__ == "__main__":
    p = Tools.PrometheusMetricServer(port=8876)
    c = p.NewCounterWithLabel(
        "test_counter", 
        ["label1", "label2"], # Two labels, will display with this order
        "test counter metric"
    )
    g = p.NewGaugeWithLabel(
        "test_gauge", 
        ["label1", "label2"], # Two labels, will display with this order
        "test gauge metric"
    )
    while True:
        c.Add({"label2": "value2", "label1": "value1"}) # Order is not matter
        c.Add(["l3", "l4"])
        c.Add(["l5"]) # Will be "l5" and ""
        c.Add(["l6", "l7", "l8"]) # Will be "l7" and "l8"
        g.Set(["l6", "l7", "l8"], Random.Int(0, 100))
        Time.Sleep(1)