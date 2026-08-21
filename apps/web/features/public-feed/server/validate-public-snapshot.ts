import Ajv2020 from "ajv/dist/2020";
import addFormats from "ajv-formats";
import schema from "../../../../../contracts/public-feed.schema.json";
import type { PublicFeedSnapshot } from "../types/public-feed";

const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validate = ajv.compile(schema);

export function validatePublicSnapshot(value: unknown): PublicFeedSnapshot {
  if (!validate(value)) {
    const message = ajv.errorsText(validate.errors, { separator: "; " });
    throw new Error(`Invalid public feed snapshot: ${message}`);
  }
  return value as unknown as PublicFeedSnapshot;
}
