// Streaming audit for the one-node/one-edge-per-line frozen VPR XML export.
#include <charconv>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

int number(const std::string& line, const std::string& field) {
    auto pos = line.find(field + "=\"");
    if (pos == line.npos) throw std::runtime_error("Missing " + field);
    const char* first = line.data() + pos + field.size() + 2;
    int value;
    auto parsed = std::from_chars(first, line.data()+line.size(), value);
    if (parsed.ec != std::errc{} || *parsed.ptr != '"' || value < 0)
        throw std::runtime_error("Invalid " + field);
    return value;
}
struct Span {int low, high;};
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::ifstream file(argv[1]);
    std::vector<Span> spans;
    std::set<int> layers;
    std::string line;
    long long intra=0, spanning=0, vertical=0, disjoint=0;
    while (std::getline(file,line)) {
        if (line.rfind("<node ",0)==0) {
            if (number(line,"id") != int(spans.size())) throw std::runtime_error("Non-dense IDs");
            int low=number(line,"layer_low"), high=number(line,"layer_high");
            spans.push_back({low,high});
            for(int layer=low;layer<=high;++layer) layers.insert(layer);
            vertical += line.find("type=\"CHANZ\"") != line.npos;
        } else if (line.rfind("<edge ",0)==0) {
            auto a=spans.at(number(line,"src_node")), b=spans.at(number(line,"sink_node"));
            if (a.low==a.high && b.low==b.high && a.low==b.low) ++intra;
            else ++spanning;
            disjoint += a.high<b.low || b.high<a.low;
        }
    }
    if (!file.eof() || spans.empty() || !intra) return 1;
    std::cout<<layers.size()<<','<<spans.size()<<','<<intra+spanning<<','<<intra<<','<<spanning<<','<<disjoint<<','<<vertical<<'\n';
}
