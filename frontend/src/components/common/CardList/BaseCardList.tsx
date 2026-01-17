import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw, Search, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";

export interface BaseCardListProps<T> {
  items: T[];
  onSync?: () => Promise<void>;
  onSearch?: (query: string) => void;
  loading?: boolean;
  createUrl?: string;
  showSync?: boolean; // Option pour afficher/masquer le bouton de sync
}

export abstract class BaseCardList<T extends { id: string }> extends React.Component<BaseCardListProps<T>, { searchQuery: string; syncing: boolean }> {
  state = {
    searchQuery: "",
    syncing: false,
  };

  abstract renderCard(item: T): React.ReactNode;
  abstract getEmptyMessage(): string;
  abstract getSyncButtonLabel(): string;
  abstract getCreateButtonLabel(): string;

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
    const { loading, createUrl, showSync = true } = this.props;
    const { syncing, searchQuery } = this.state;
    const filteredItems = this.filterItems();

    return (
      <div className="relative space-y-3 sm:space-y-2">
        {/* Header with search, create button and sync */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex gap-2 flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input placeholder="Search..." value={searchQuery} onChange={this.handleSearch} className="pl-10" />
            </div>

            {createUrl && (
              <a href={createUrl}>
                <Button variant="outline" className="h-10 w-10 sm:w-auto p-0 sm:px-4" title={this.getCreateButtonLabel()}>
                  <Plus className="h-4 w-4 sm:mr-2" />
                  <span className="hidden sm:inline">{this.getCreateButtonLabel()}</span>
                </Button>
              </a>
            )}
          </div>

          {showSync && this.props.onSync && (
            <Button onClick={this.handleSync} disabled={syncing || loading} variant="outline" className="w-full sm:w-auto">
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? "animate-spin" : ""}`} />
              {this.getSyncButtonLabel()}
            </Button>
          )}
        </div>

        {/* Cards grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-6 sm:py-8 text-gray-500">
            <img src="/logo_ticket_code.svg" alt="Loading" className="h-12 w-12 sm:h-16 sm:w-16 mb-3 sm:mb-4 animate-pulse" />
            <p>Loading...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 sm:py-8 text-gray-500">
            <img src="/logo_ticket_code.svg" alt="No items" className="h-12 w-12 sm:h-16 sm:w-16 mb-3 sm:mb-4 opacity-50" />
            <p className="text-center px-4">{this.getEmptyMessage()}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {filteredItems.map((item) => (
              <div key={item.id}>{this.renderCard(item)}</div>
            ))}
          </div>
        )}
      </div>
    );
  }
}
