import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw, Search } from "lucide-react";

export interface BaseCardListProps<T> {
  items: T[];
  onSync?: () => Promise<void>;
  onSearch?: (query: string) => void;
  loading?: boolean;
}

export abstract class BaseCardList<T extends { id: string }> extends React.Component<BaseCardListProps<T>, { searchQuery: string; syncing: boolean }> {
  state = {
    searchQuery: "",
    syncing: false,
  };

  abstract renderCard(item: T): React.ReactNode;
  abstract getEmptyMessage(): string;
  abstract getSyncButtonLabel(): string;

  handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    this.setState({ searchQuery: query });
    this.props.onSearch?.(query);
  };

  handleSync = async () => {
    if (!this.props.onSync) return;

    this.setState({ syncing: true });
    try {
      await this.props.onSync();
    } finally {
      this.setState({ syncing: false });
    }
  };

  filterItems(): T[] {
    const { items } = this.props;
    const { searchQuery } = this.state;

    if (!searchQuery) return items;

    return items.filter((item) => JSON.stringify(item).toLowerCase().includes(searchQuery.toLowerCase()));
  }

  render() {
    const { loading } = this.props;
    const { syncing, searchQuery } = this.state;
    const filteredItems = this.filterItems();

    return (
      <div className="space-y-4">
        {/* Header with search and sync */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input placeholder="Search..." value={searchQuery} onChange={this.handleSearch} className="pl-10" />
          </div>

          {this.props.onSync && (
            <Button onClick={this.handleSync} disabled={syncing || loading} variant="outline">
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? "animate-spin" : ""}`} />
              {this.getSyncButtonLabel()}
            </Button>
          )}
        </div>

        {/* Cards grid */}
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500">{this.getEmptyMessage()}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => (
              <div key={item.id}>{this.renderCard(item)}</div>
            ))}
          </div>
        )}
      </div>
    );
  }
}
