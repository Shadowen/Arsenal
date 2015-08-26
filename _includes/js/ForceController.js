myApp.controller('ForceController', function($scope, $routeParams) {
    // Create a custom force directed graph
    function createForce() {
        var self = this;
        // Add a node with the specified properties.
        // Visible and focused by default
        self.addNode = function(version, id, name, size) {
            allNodes.push({
                version: version,
                id: id,
                name: name,
                size: size,
                focus: true,
                visible: true,
            });
            // Make sure to do a full update
            versionChanged = true;
            linkMinimumChanged = true;
            return self;
        };
        // Remove the specified node
        self.removeNode = function(version, id) {
            var i = 0;
            var n = findNode(version, id);
            while (i < allLinks.length) {
                if ((allLinks[i]['source'] == n) || (allLinks[i]['target'] == n)) {
                    allLinks.splice(i, 1);
                } else i++;
            }
            allNodes.splice(findNodeIndex(version, id), 1);
            // Make sure to do a full update later
            versionChanged = true;
            linkMinimumChanged = true;
            return self;
        };
        // Add a link between two nodes by id. Only works within a version
        self.addLink = function(version, source, target, strength) {
            allLinks.push({
                version: version,
                "source": findNode(version, source),
                "target": findNode(version, target),
                "value": strength,
                focus: true,
                visible: true
            });
            // Make sure to do a full update
            versionChanged = true;
            linkMinimumChanged = true;
            return self;
        };
        // Appends the root svg element of the force-directed graph to the specified parent
        self.appendTo = function(parent) {
            parent.appendChild(svg[0][0]);
            return self;
        };
        // Get or set the version of the graph
        self.version = function(v) {
            if (typeof arguments[0] === 'undefined') {
                return versionValue;
            }
            versionValue = v;
            versionChanged = true;
            return self;
        };
        // Gets or sets the minimum strength of link displayed
        self.linkMinimum = function(min) {
            if (typeof arguments[0] === 'undefined') {
                return linkMinimumValue;
            }
            linkMinimumValue = min;
            linkMinimumChanged = true;
            return self;
        }

        // -- Private functions
        var findNode = function(version, id) {
            for (var i = 0; i < allNodes.length; i++) {
                if (allNodes[i].id === id && allNodes[i].version === version) {
                    return allNodes[i];
                }
            };
        };

        var findNodeIndex = function(version, id) {
            for (var i = 0; i < allNodes.length; i++) {
                if (allNodes[i].id == id && allNodes[i].version === version) {
                    return i;
                }
            };
        };

        var findLink = function(source, target) {
            for (var i = 0; i < allLinks.length; i++) {
                var link = allLinks[i];
                if (link.source.id == source && link.target.id == target) {
                    return link;
                } else if (link.source.id == target && link.target.id == source) {
                    return link;
                }
            }
            return null;
        }

        var findNodeLinks = function(source, bothVersions) {
            var retLinks = [];
            if (bothVersions) {
                for (var i = 0; i < allLinks.length; i++) {
                    if (allLinks[i].source.id == source.id || allLinks[i].target.id == source.id) {
                        retLinks.push(allLinks[i]);
                    }
                }
            } else {
                for (var i = 0; i < allLinks.length; i++) {
                    if (allLinks[i].source == source || allLinks[i].target == source) {
                        retLinks.push(allLinks[i]);
                    }
                }
            }
            return retLinks;
        }

        var nodeColor = d3.scale.category20()
            .domain([0, 9999]);;
        var linkColor = d3.scale.category20c();
        var unfocusedOpacity = 0.1;
        var tooltipTextPadding = 10;
        var transitionSpeed = 500;

        // set up the D3 visualisation in the specified element
        var w = $('#force-container').width(),
            h = $('#force-container').height();

        var svg = d3.select(document.createElementNS("http://www.w3.org/2000/svg", "svg"))
            .attr('id', 'svg')
            .attr("width", w)
            .attr("height", h);
        var vis = svg
            .append('svg:g');

        var force = d3.layout.force();

        var allLinks = [];
        var allNodes = [];

        var focused = false;
        var focusedNode;
        var versionChanged;
        var linkMinimumChanged;
        var versionValue;
        var linkMinimumValue;

        self.update = function() {
            // The nodes and links on the graph at the moment.
            var nodes;
            var links;
            // Update nodes and links if the version has changed
            if (versionChanged) {
                nodes = allNodes.filter(function(n) {
                    return n.version === versionValue;
                });
                // TODO make more efficient
                for (var i = 0; i < nodes.length; i++) {
                    for (var j = 0; j < allNodes.length; j++) {
                        if (allNodes[j].version == versionValue) {
                            continue;
                        }
                        if (nodes[i].id === allNodes[j].id) {
                            nodes[i].x = allNodes[j].x;
                            nodes[i].y = allNodes[j].y;
                        }
                    }
                }
                links = allLinks.filter(function(l) {
                    return l.version === versionValue;
                });
                force.nodes(nodes);
                force.links(links);
                versionChanged = false;
            } else {
                nodes = force.nodes();
                links = force.links();
            }

            // Scales that we will use to draw the graph
            var linkSizes = allLinks.map(function(l) {
                return l.value;
            });
            var smallestLink = d3.min(linkSizes);
            var largestLink = d3.max(linkSizes);
            var linkStrengthScale = d3.scale.linear()
                .domain([0, largestLink])
                .range([0, 1]);
            var strokeScale = d3.scale.pow()
                .exponent(3)
                .domain([smallestLink, largestLink])
                .range([1, 10]);
            var linkDistanceScale = d3.scale.linear()
                .domain([smallestLink, largestLink])
                .range([300, 70]);
            var nodeSizeScale = d3.scale.pow()
                .exponent(2)
                .domain([0, 1])
                .range([10, 100]);
            linkColor.domain([smallestLink, largestLink]);

                // Make links under the minimum linkage value
            if (linkMinimumChanged) {
                for (var linkNum = 0; linkNum < allLinks.length; linkNum++) {
                    var l = allLinks[linkNum];
                    if (l.value < linkMinimumValue) {
                        l.visible = false;
                    } else {
                        l.visible = true;
                    }
                }
                // Make nodes that don't have any links invisible
                for (var i = 0; i < allNodes.length; i++) {
                    var n = allNodes[i];
                    if (!findNodeLinks(n).reduce(function(prev, curr) {
                            return prev || curr.visible;
                        }, false)) {
                        n.visible = false;
                    } else {
                        n.visible = true;
                    }
                }
                linkMinimumChanged = false;
            }

            // Update focused nodes
            if (!focused) {
                for (var i = 0; i < allNodes.length; i++) {
                    allNodes[i].focus = true;
                }
                for (var linkNum = 0; linkNum < allLinks.length; linkNum++) {
                    allLinks[linkNum].focus = true;
                }
            } else {
                // Focus an element
                for (var i = 0; i < allNodes.length; i++) {
                    allNodes[i].focus = false;
                }
                for (var linkNum = 0; linkNum < allLinks.length; linkNum++) {
                    allLinks[linkNum].focus = false;
                }
                findNodeLinks(focusedNode, true).forEach(function(l) {
                    if (l.visible) {
                        l.focus = true;
                        l.source.focus = true;
                        l.target.focus = true;
                    }
                });
            }

            // Create links
            var link = vis.selectAll("line")
                .data(links, function(d) {
                    return d.source.id + "-" + d.target.id;
                });
            link.enter().append("line")
                .attr("id", function(d) {
                    return d.source.id + "-" + d.target.id;
                })
                .classed("link", true)
                .attr('stroke-width', 0);
            link
                .transition()
                .duration(transitionSpeed)
                .attr('visibility', function(d) {
                    return d.visible ? 'visible' : 'hidden';
                })
                .attr('stroke', function(d) {
                    return linkColor(d.value);
                })
                .attr("stroke-width", function(d) {
                    return d.visible ? strokeScale(d.value) : 0;
                })
                .attr('opacity', function(d) {
                    return d.focus ? 1 : unfocusedOpacity;
                });
            link.exit()
                .transition()
                .duration(transitionSpeed)
                .attr('stroke-width', 0)
                .remove();
            // Create nodes
            var node = vis.selectAll("g.node")
                .data(nodes, function(d) {
                    return d.id;
                });
            var nodeEnter = node.enter()
                .append("g")
                .classed("node", true)
                .classed('send-to-top', true)
                .append('a')
                .attr('xlink:href', function(d) {
                    return '{{ site.baseurl }}/#/item/' + d.id;
                })
                .call(force.drag)
                .on('mouseenter', function(d) {
                    focused = !focused;
                    focusedNode = d;

                    var tooltip = svg.append("g")
                        .classed('tooltip', true)
                        .attr('opacity', 0);
                    var text = tooltip.append('text')
                        .attr('fill', 'rgba(255,255,0,1)');
                    text.append('tspan')
                        .attr('x', 0)
                        .attr('dy', '1.2em')
                        .text(d.name);
                    text.append('tspan')
                        .attr('x', 0)
                        .attr('dy', '1.2em')
                        .text('Win Rate: ' + (d.size * 100).toFixed(2) + '%');
                    var textBBox = text.node().getBBox();
                    tooltip.append('rect')
                        .classed('tooltip-bg', true)
                        .attr('x', textBBox.x - tooltipTextPadding)
                        .attr('y', textBBox.y - tooltipTextPadding)
                        .attr('width', textBBox.width + 2 * tooltipTextPadding)
                        .attr('height', textBBox.height + 2 * tooltipTextPadding)
                        .attr('rx', tooltipTextPadding / 2)
                        .attr('ry', tooltipTextPadding / 2);
                    $(tooltip.node()).children('text').detach().appendTo(tooltip.node());
                    tooltip
                        .transition()
                        .attr('opacity', 1);
                    update();
                })
                .on('mousemove', function(d) {
                    if (!d.focus) {
                        return;
                    }
                    var node = svg.selectAll('g.tooltip text')
                        .node();
                    if (typeof node === 'undefined') {
                        return;
                    }
                    var textBBox = node.getBBox();
                    var x = Math.min(d.x + d3.mouse(this)[0] + tooltipTextPadding, w - textBBox.width);
                    var y = Math.max(d.y + d3.mouse(this)[1] - tooltipTextPadding - textBBox.height, 0);
                    svg.selectAll('g.tooltip')
                        .attr("transform", "translate(" + x + ', ' + y + ")");
                })
                .on('mouseleave', function(d) {
                    focused = false;

                    svg.selectAll('g.tooltip')
                        .transition()
                        .attr('opacity', 0)
                        .remove()
                    update();
                })
                .append('g')
                .classed('hover-scale', true);
            node
                .attr('pointer-events', function(d) {
                    return d.focus ? 'all' : 'none';
                })
            node.exit()
                .transition()
                .remove();
            nodeEnter.append("svg:circle")
                .attr("id", function(d) {
                    return "Node;" + d.id;
                })
                .attr('stroke', 'none')
                .attr('r', 0);
            node.select('circle')
                .attr("fill", function(d) {
                    return nodeColor(d.id);
                })
                .transition()
                .duration(transitionSpeed)
                .attr('visiblility', function(d) {
                    return d.visible ? 'visible' : 'hidden';
                })
                .attr("r", function(d) {
                    return d.visible ? nodeSizeScale(d.size) : 0;
                })
                .attr('opacity', function(d) {
                    return d.focus ? 1 : unfocusedOpacity;
                });
            node.exit().select('circle')
                .transition()
                .duration(transitionSpeed)
                .attr('r', 0)
                .remove();
            nodeEnter.append('defs')
                .append('clipPath')
                .attr('id', function(d) {
                    return 'circle' + d.version + ':' + d.id;
                })
                .append('circle')
                .attr('r', 0);
            node.select('defs>clipPath>circle')
                .transition()
                .duration(transitionSpeed)
                .attr("r", function(d) {
                    return d.visible ? nodeSizeScale(d.size) / 1.2 : 0;
                });
            node.exit().select('defs>clipPath>circle')
                .transition()
                .duration(transitionSpeed)
                .attr('r', 0)
                .remove();
            nodeEnter.append('image')
                .attr('clip-path', function(d, i) {
                    return 'url(#circle' + d.version + ':' + d.id + ')';
                })
                .attr('xlink:href', function(d) {
                    return 'http://ddragon.leagueoflegends.com/cdn/' + d.version + '.1/img/item/' + d.id + '.png'
                });
            node.select('image')
                .transition()
                .duration(transitionSpeed)
                .attr('width', function(d) {
                    return d.visible ? 2 * nodeSizeScale(d.size) / 1.2 : 0;
                })
                .attr('height', function(d) {
                    return d.visible ? 2 * nodeSizeScale(d.size) / 1.2 : 0;
                })
                .attr('x', function(d) {
                    return d.visible ? -nodeSizeScale(d.size) / 1.2 : 0;
                })
                .attr('y', function(d) {
                    return d.visible ? -nodeSizeScale(d.size) / 1.2 : 0;
                }).attr('opacity', function(d) {
                    return d.focus ? 1 : unfocusedOpacity;
                });;
            node.exit().select('image')
                .transition()
                .duration(transitionSpeed)
                .attr('width', 0)
                .attr('height', 0)
                .attr('x', 0)
                .attr('y', 0)
                .remove();

            // because of the way the network is created, nodes are created first, and links second,
            // so the lines were on top of the nodes, this just reorders the DOM to put the svg:g on top
            $(".send-to-top").each(function(index) {
                this.parentNode.appendChild(this);
            });
            // Send tooltips to very top
            $('.tooltip').each(function(index) {
                this.parentNode.appendChild(this);
            });

            force.on("tick", function() {
                node.attr("transform", function(d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });

                link.attr("x1", function(d) {
                        return d.source.x;
                    })
                    .attr("y1", function(d) {
                        return d.source.y;
                    })
                    .attr("x2", function(d) {
                        return d.target.x;
                    })
                    .attr("y2", function(d) {
                        return d.target.y;
                    });
            });

            // Restart the force layout.
            force
                .gravity(0.5)
                // Invisible nodes do not interact
                .charge(function(d) {
                    return d.visible ? -20000 : 0;
                })
                .friction(0.1)
                .linkDistance(function(d) {
                    return d.source.size + d.target.size + linkDistanceScale(findLink(d.source.id, d.target.id).value);
                })
                // Invisible nodes do not interact
                .linkStrength(function(d) {
                    return d.visible ? d.focus ? linkStrengthScale(d.value) : linkStrengthScale(d.value) / 2 : 0;
                })
                // Set the size to current svg size
                .size([$('#force-container').width(), $('#force-container').height()])
                .start();
            return self;
        };

        // Make it all go
        return self.version('5.14')
            .linkMinimum(0.3);
    }


    var theSvg = $('#force-container').append($('<svg>')
        .attr('id', 'theSvg'));

    // Title
    d3.select($('#theSvg')[0]).append('div')
        .attr('id', 'title')
        .style('pointer-events', 'none')
        .style('position', 'absolute')
        .style('top', '50%')
        .style('left', '20px')
        .style('font-family', 'sans-serif')
        .style('font-size', 'larger')
        .style('text-align', 'center')
        .append('div')
        .classed('trans-bg', true)
        .style('transform-origin', 'left')
        .style('transform', 'rotate(-90deg) translateX(-50%) translateY(50%)')
        .text('Arsenal')
        .append('div')
        .style('dy', '1.2em')
        .text('Item win rate and co-occurance visualizer');

    // Info text
    var infoText = d3.select($('#theSvg')[0]).append('div')
        .attr('id', 'info')
        .classed('trans-bg', true)
        .style('pointer-events', 'none')
        .style('position', 'absolute')
        .style('width', '30%')
        .style('bottom', '20px')
        .style('left', '20px')
        .html('The size of an item represents its win rate.<br>The lines represent the frequency of items being found together.<br>Double click to focus on an item.');

    // Legal stuff
    var legalText = d3.select($('#theSvg')[0]).append('div')
        .attr('id', 'legal-info')
        .style('pointer-events', 'none')
        .style('position', 'absolute')
        .style('width', '38%')
        .style('bottom', '20px')
        .style('right', '20px')
        .style('font-size', 'smaller')
        .style('text-align', 'right')
        .html('This application isn\'t endorsed by Riot Games and doesn\'t reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends &copy; Riot Games, Inc.');


    // The graph
    var graph = createForce()
        .appendTo($('#theSvg')[0])
        .update();
    $(function() {
        $(window).resize(function() {
            $('#theSvg,#svg')
                .attr('width', $('#force-container').width())
                .attr('height', $('#force-container').height());
            graph.update();
        });
    });

    // Link minimum slider
    var linkMinSlider = d3.select($('#theSvg')[0]).append('div')
        .style('position', 'absolute')
        .style('width', '70%')
        .style('top', '20px')
        .style('left', '20px')
    linkMinSlider.append('div')
        .style('pointer-events', 'none')
        .style('position', 'absolute')
        .style('top', '40px')
        .text('Minimum co-occurance rate')
    var linkMinDisplay = d3.scale.linear().domain([0, 1]).range([0, 1]);
    linkMinSlider.append('div')
        .call(d3.slider()
            .scale(linkMinDisplay)
            .axis(true)
            .snap(true)
            .value(graph.linkMinimum())
            .on('slide', function(evt, value) {
                graph
                    .linkMinimum(value)
                    .update();
            })
        );

    // Version slider
    var versionSlider = d3.select($('#theSvg')[0]).append('div')
        .style('position', 'absolute')
        .style('width', '20%')
        .style('top', '20px')
        .style('right', '20px');
    versionSlider.append('div')
        .style('pointer-events', 'none')
        .style('position', 'absolute')
        .style('top', '40px')
        .style('right', '20px')
        .text('Game Version');
    versionSlider.append('div')
        .call(d3.slider()
            .scale(d3.scale.ordinal()
                .domain([5.11, 5.14])
                .rangePoints([0, 1], 0.5))
            .axis(d3.svg.axis())
            .value(graph.version())
            .on('slide', function(evt, value) {
                graph.version('' + value)
                    .update();
            })
        );

    //------------------------------------
    //----Splash screen
    //------------------------------------
    if (!$routeParams.nosplash) {
        d3.select('#theSvg')
            .style("opacity", 0);

        var $bg = $('<div>')
            .attr('id', 'bg')
            .css('position', 'absolute')
            .css('top', 0)
            .css('bottom', 0)
            .css('left', 0)
            .css('right', 0)
            .css('background-image', 'url(\'{{ site.baseurl }}/images/bg.png\')')
            .css('background-size', 'cover')
            .on('click', function() {
                // Click to skip splash screen
                transitionIn();
            })
            .appendTo("#force-container");
        $(window)
            .resize(function() {
                if (($(this).width() / $(this).height()) < $bg.width() / $bg.height()) {
                    $bg
                        .removeClass()
                        .addClass('bgheight');
                } else {
                    $bg
                        .removeClass()
                        .addClass('bgwidth');
                }
            })
            .trigger("resize");

        var transitionIn = function() {
            // Transition the splash screen out
            d3.select("#bg").transition()
                .duration(1000)
                .style("opacity", 0)
                .each("end", function() {
                    d3.select(this)
                        .remove();
                });
            // Transition the graph in
            d3.select('#theSvg').transition()
                .delay(500)
                .duration(1000)
                .style("opacity", 1)
        };
        setTimeout(transitionIn, 2000);
    }

    // Load data
    $.getJSON('{{site.baseurl}}/data/itemCross.json').then(function(data) {
        for (var i = 0; i < data.nodes.length; i++) {
            var node = data.nodes[i];
            // if (!node.version || !node.id || !node.name || typeof node.winRate === 'undefined') {
            //     console.error('Node', node, 'has a problem!');
            //     continue;
            // }
            graph.addNode(node.version, node.id, node.name, node.winRate);
        };
        for (var i = 0; i < data.links.length; i++) {
            var link = data.links[i];
            // if (!link.version || !link.source || !link.target || !link.value) {
            //     console.error('Link', link, 'has a problem!');
            //     continue;
            // }
            graph.addLink(link.version, link.source, link.target, link.value);
        };
        graph.version('5.14')
            .update();
    });
});
