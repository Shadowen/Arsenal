myApp.controller('ItemController', function($scope, $routeParams) {
    $.getJSON('{{site.baseurl}}/data/itemStats.json').then(function(data) {
        var dataArray = [];
        dataArray.push({
            title: property,
            values: [data[$routeParams.itemId][property], data[$routeParams.itemId][property]]
        });
        barComparison.data(dataArray);
    });

    var createHorizontalBarComparison = function(parent) {
        var data = [];
        var margins = {
            top: 10,
            bottom: 10,
            sides: 10,
        };
        var titleValue = ['Buy Time'];
        var titleHeight = 60;

        var centerOffset;
        var barHeight = 40;
        var barSpacing = 10;
        // Below this size, the value text will render outside the box
        var minimumBarSize = 100;
        var xScale;

        // The root SVG element of the graph
        var svg = parent
            .append('svg')
            .classed('chart', true);
        // Tooltip
        var tip = d3.tip()
            .attr('class', 'd3-tip')
            .offset([-10, 0])
            .html(function(d, i, a) {
                return d.values[a];
            });
        svg.call(tip);
        // Create the "chart" - obeys margins
        var chart = svg.append("g")
            .attr("transform", "translate(0," + margins.top + ")");
        // Create title
        var titleElement = chart.append('text')
            .classed('title', true)
            .attr('y', 50)
            .style('text-anchor', 'middle');
        // Create the body of the chart
        var chartArea = chart.append("g")
            .attr("transform", 'translate(0, ' + titleHeight + ')');

        var update = function() {
            // Recalculate some parameters
            var width = 640 + 2 * margins.sides;
            var height = margins.top + titleHeight + data.length * barHeight - barSpacing + margins.bottom;
            var halfWidth = width / 2;
            centerOffset = 12 * d3.max(data.map(function(d) {
                return d.title.length;
            })) + 20;
            xScale = d3.scale.linear()
                .domain([0, d3.max(data.map(function(d) {
                    return d3.max(d.values);
                }))])
                .range([0, halfWidth - centerOffset - margins.sides]);
            // Update the SVG's total size
            svg.attr('width', width);
            svg.attr('height', height);

            // Update title
            titleElement
                .attr('x', halfWidth)
                .text(titleValue);
            // Create each row
            var row = chartArea.selectAll("g")
                .data(data)
                .enter()
                .append("g")
                .attr('transform', function(d, i) {
                    return 'translate(0, ' + barHeight * i + ')';
                });
            row.append("rect")
                .classed("row", true)
                .attr("width", width)
                .attr("height", barHeight);
            var rowLabel = row.append('text')
                .classed('category-label', true)
                .attr("x", halfWidth)
                .attr('y', barHeight / 2)
                .attr("dy", ".35em")
                .text(function(d) {
                    return d.title;
                });
            var leftBar = row
                .append("rect")
                .classed('bar-left', true)
                .attr('transform', 'translate(' + halfWidth + ') scale(-1, 1)');
            var rightBar = row
                .append("rect")
                .classed('bar-right', true)
                .attr('transform', 'translate(' + halfWidth + ')');
            var bars = leftBar.union(rightBar)
                .classed('bar', true)
                .classed('emphasis', function(d, i, side) {
                    return d.values[side] >= d.values[side ^ 1];
                })
                .attr('height', barHeight - barSpacing)
                .attr('x', centerOffset)
                .attr('y', barSpacing / 2)
                .attr('width', 0)
                .on('mouseover', tip.show)
                .on('mouseout', tip.hide);
            bars
                .transition()
                .delay(function(d, i) {
                    return i * 300;
                })
                .duration(500)
                .attr('width', function(d, i, side) {
                    return xScale(d.values[side]);
                });


            var leftValueText = row.append('text')
                .attr('x', -centerOffset)
                .attr('dx', function(d) {
                    return xScale(d.values[0]) > minimumBarSize ? 5 : -5;
                })
                .style('text-anchor', function(d) {
                    return xScale(d.values[0]) > minimumBarSize ? 'begin' : 'end';
                })
                .text(function(d) {
                    return d.values[0];
                });
            leftValueText.transition()
                .delay(function(d, i) {
                    return i * 300;
                })
                .duration(500)
                .attr('x', function(d) {
                    return -xScale(d.values[0]) - centerOffset;
                }).tween('text', function(d) {
                    var i = d3.interpolateRound(0, d.values[0]);
                    return function(t) {
                        this.textContent = i(t);
                    };
                });
            var rightValueText = row.append('text')
                .attr('x', centerOffset)
                .attr('dx', function(d) {
                    return xScale(d.values[1]) > minimumBarSize ? -5 : 5;
                })
                .style('text-anchor', function(d) {
                    return xScale(d.values[1]) > minimumBarSize ? 'end' : 'begin';
                })
                .text(function(d) {
                    return d.values[1];
                });
            rightValueText.transition()
                .delay(function(d, i) {
                    return i * 300;
                })
                .duration(500)
                .attr('x', function(d, row, side) {
                    return xScale(d.values[1]) + centerOffset;
                }).tween('text', function(d) {
                    var i = d3.interpolateRound(0, d.values[1]);
                    return function(t) {
                        this.textContent = i(t);
                    };
                });
            var valueText = leftValueText.union(rightValueText)
                .attr('transform', 'translate(' + halfWidth + ',0)')
                .attr('y', barHeight / 2 + barSpacing)
                .attr('dy', -5);
            return obj;
        };
        // Exports
        var obj = function barComparison() {
            return svg[0][0];
        };
        obj.title = function(newTitle) {
            titleValue[0] = newTitle;
            obj.update();
            return obj;
        };
        obj.data = function(newData) {
            console.log(newData);
            data = newData;
            obj.update();
            return obj;
        }
        obj.update = update;
        return obj
    }
    var barComparison = createHorizontalBarComparison(d3.select('#item-container'));
    barComparison.data([{
        title: "Top 10%",
        values: [32314, 100000]
    }, {
        title: "Average",
        values: [112394, 50000]
    }, {
        title: "Median",
        values: [2433, 12310]
    }]);

});
