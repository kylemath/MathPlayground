#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

using Grid = std::array<int, 16>;
using Row = std::array<int, 4>;

struct RowGroup {
    std::uint32_t mask;
    std::vector<Row> permutations;
};

Grid rotate_clockwise(const Grid& grid) {
    Grid result{};
    for (int row = 0; row < 4; ++row) {
        for (int column = 0; column < 4; ++column) {
            result[row * 4 + column] = grid[(3 - column) * 4 + row];
        }
    }
    return result;
}

Grid reflect_left_right(const Grid& grid) {
    Grid result{};
    for (int row = 0; row < 4; ++row) {
        for (int column = 0; column < 4; ++column) {
            result[row * 4 + column] = grid[row * 4 + (3 - column)];
        }
    }
    return result;
}

std::set<Grid> d4_images(const Grid& grid) {
    std::set<Grid> images;
    Grid current = grid;
    for (int rotation = 0; rotation < 4; ++rotation) {
        images.insert(current);
        images.insert(reflect_left_right(current));
        current = rotate_clockwise(current);
    }
    return images;
}

Grid canonical(const Grid& grid) {
    const auto images = d4_images(grid);
    return *images.begin();
}

std::vector<RowGroup> make_row_groups() {
    std::vector<RowGroup> groups;
    for (int a = 1; a <= 13; ++a) {
        for (int b = a + 1; b <= 14; ++b) {
            for (int c = b + 1; c <= 15; ++c) {
                for (int d = c + 1; d <= 16; ++d) {
                    if (a + b + c + d != 34) {
                        continue;
                    }
                    Row row{a, b, c, d};
                    RowGroup group{};
                    group.mask = (1u << (a - 1)) | (1u << (b - 1))
                               | (1u << (c - 1)) | (1u << (d - 1));
                    do {
                        group.permutations.push_back(row);
                    } while (std::next_permutation(row.begin(), row.end()));
                    groups.push_back(std::move(group));
                }
            }
        }
    }
    return groups;
}

int main(int argc, char** argv) {
    const auto groups = make_row_groups();
    std::map<std::uint32_t, std::size_t> group_by_mask;
    for (std::size_t index = 0; index < groups.size(); ++index) {
        group_by_mask[groups[index].mask] = index;
    }

    constexpr std::uint32_t full_mask = (1u << 16) - 1u;
    std::set<Grid> oriented;
    std::uint64_t candidate_row_partitions = 0;

    for (const auto& group0 : groups) {
        for (const auto& group1 : groups) {
            if ((group0.mask & group1.mask) != 0) {
                continue;
            }
            for (const auto& group2 : groups) {
                if (((group0.mask | group1.mask) & group2.mask) != 0) {
                    continue;
                }
                const auto mask3 = full_mask ^ (group0.mask | group1.mask | group2.mask);
                const auto found = group_by_mask.find(mask3);
                if (found == group_by_mask.end()) {
                    continue;
                }
                ++candidate_row_partitions;

                for (const auto& row0 : group0.permutations) {
                    for (const auto& row1 : group1.permutations) {
                        for (const auto& row2 : group2.permutations) {
                            Row row3{};
                            std::uint32_t observed_mask = 0;
                            bool valid = true;
                            for (int column = 0; column < 4; ++column) {
                                const int value = 34 - row0[column] - row1[column] - row2[column];
                                if (value < 1 || value > 16) {
                                    valid = false;
                                    break;
                                }
                                const auto bit = 1u << (value - 1);
                                if ((observed_mask & bit) != 0) {
                                    valid = false;
                                    break;
                                }
                                observed_mask |= bit;
                                row3[column] = value;
                            }
                            if (!valid || observed_mask != mask3) {
                                continue;
                            }
                            if (row0[0] + row1[1] + row2[2] + row3[3] != 34
                                || row0[3] + row1[2] + row2[1] + row3[0] != 34) {
                                continue;
                            }
                            Grid grid{};
                            for (int column = 0; column < 4; ++column) {
                                grid[column] = row0[column];
                                grid[4 + column] = row1[column];
                                grid[8 + column] = row2[column];
                                grid[12 + column] = row3[column];
                            }
                            oriented.insert(grid);
                        }
                    }
                }
            }
        }
    }

    std::set<Grid> canonicals;
    std::map<std::size_t, std::size_t> orbit_histogram;
    for (const auto& grid : oriented) {
        canonicals.insert(canonical(grid));
    }
    for (const auto& grid : canonicals) {
        ++orbit_histogram[d4_images(grid).size()];
    }

    std::ostringstream output;
    output << "{\n"
           << "  \"method\": \"ordered 34-sum row partitions with forced fourth row\",\n"
           << "  \"row_value_sets_summing_to_34\": " << groups.size() << ",\n"
           << "  \"ordered_candidate_row_partitions\": " << candidate_row_partitions << ",\n"
           << "  \"oriented_count\": " << oriented.size() << ",\n"
           << "  \"d4_canonical_count\": " << canonicals.size() << ",\n"
           << "  \"orbit_size_histogram\": {";
    bool first = true;
    for (const auto& [size, count] : orbit_histogram) {
        if (!first) {
            output << ", ";
        }
        output << "\"" << size << "\": " << count;
        first = false;
    }
    output << "},\n"
           << "  \"product_check\": "
           << ((canonicals.size() * 8 == oriented.size()) ? "true" : "false") << "\n"
           << "}\n";

    std::cout << output.str();
    if (argc > 1) {
        std::ofstream file(argv[1]);
        file << output.str();
    }
    if (argc > 2) {
        std::ofstream file(argv[2]);
        for (const auto& grid : canonicals) {
            for (std::size_t index = 0; index < grid.size(); ++index) {
                if (index != 0) {
                    file << ',';
                }
                file << grid[index];
            }
            file << '\n';
        }
    }
    return oriented.size() == 7040 && canonicals.size() == 880 ? 0 : 1;
}
